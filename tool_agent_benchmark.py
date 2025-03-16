#!/usr/bin/env python3

import json
import time
import argparse
import csv
import sys
from typing import List, Dict, Any, Union, Tuple
from datetime import datetime

from tool_agent import ToolAgent

class ToolAgentBenchmark:
    """Benchmark tool for evaluating ToolAgent performance"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash", verbose: bool = False):
        """Initialize the benchmark tool
        
        Args:
            model_name (str): The model to use for benchmarking
            verbose (bool): Whether to output detailed logging
        """
        self.model_name = model_name
        self.verbose = verbose
        self.agent = ToolAgent(model_name=model_name)
        self.results = []
        self.overall_token_usage = {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0
        }
    
    def log(self, message: str):
        """Log a message if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case and collect metrics
        
        Args:
            test_case: Dictionary containing test information
            
        Returns:
            Dictionary with test results and metrics
        """
        test_id = test_case.get('id', 'unnamed_test')
        prompt = test_case.get('prompt', '')
        expected_tools = test_case.get('expected_tools', [])
        expected_response_contains = test_case.get('expected_response_contains', [])
        
        self.log(f"\n⌛ Running test: {test_id}")
        self.log(f"Prompt: {prompt}")
        
        # Reset token usage before each test
        self.agent.reset_token_usage()
        
        # Start conversation
        start_time = time.time()
        conversation = self.agent.create_conversation()
        
        # Process the message
        result = self.agent.process_message(conversation, prompt)
        end_time = time.time()
        exec_time = end_time - start_time
        
        # Extract metrics
        tool_calls = [entry for entry in result.get('log', []) if entry.get('stage') == 'tool_call']
        tools_called = [call.get('tool') for call in tool_calls]
        
        # Get token usage from the result
        token_usage = result.get('token_usage', {})
        input_tokens = token_usage.get('input', 0)
        output_tokens = token_usage.get('output', 0)
        total_tokens = input_tokens + output_tokens
        
        # Check for expected tools
        # Required tools must be present, optional tools (prefixed with '~') don't fail the test if absent
        required_tools = [tool for tool in expected_tools if not tool.startswith('~')]
        optional_tools = [tool[1:] for tool in expected_tools if tool.startswith('~')]
        
        required_matched = all(tool in tools_called for tool in required_tools)
        optional_used = [tool for tool in optional_tools if tool in tools_called]
        
        # Test passes if all required tools are present
        tools_matched = required_matched
        
        # Check response content
        response_text = result.get('text', '')
        response_matched = all(expected_text.lower() in response_text.lower() 
                               for expected_text in expected_response_contains)
        
        # Get thought process
        thoughts = [entry.get('content', '') for entry in result.get('log', []) 
                    if entry.get('stage') in ('initial_thought', 'updated_thought')]
        
        # Determine success based on criteria
        success = tools_matched and response_matched
        
        # Compile results
        test_result = {
            'test_id': test_id,
            'prompt': prompt,
            'success': success,
            'execution_time': exec_time,
            'response': response_text,
            'tools_called': tools_called,
            'required_tools': required_tools,
            'optional_tools': optional_tools,
            'optional_tools_used': optional_used,
            'required_tools_matched': required_matched,
            'expected_response_contains': expected_response_contains,
            'response_matched': response_matched,
            'thoughts': thoughts,
            'token_usage': {
                'input': input_tokens,
                'output': output_tokens,
                'total': total_tokens
            },
            'interaction_log': result.get('log', [])
        }
        
        # Log the result
        if success:
            self.log(f"✅ Test {test_id} passed! Time: {exec_time:.2f}s, Tokens: {total_tokens}")
            if optional_used:
                self.log(f"  - Used optional tools: {optional_used}")
        else:
            self.log(f"❌ Test {test_id} failed! Time: {exec_time:.2f}s, Tokens: {total_tokens}")
            if not tools_matched:
                self.log(f"  - Tools mismatch. Required: {required_tools}, Got: {tools_called}")
            if not response_matched:
                self.log(f"  - Response didn't contain expected text: {expected_response_contains}")
        
        return test_result
    
    def run_benchmark(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run the full benchmark suite
        
        Args:
            test_cases: List of test case dictionaries
            
        Returns:
            List of summary dictionaries with test results
        """
        self.results = []
        summary_results = []
        
        # Track overall token usage
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        
        total_tests = len(test_cases)
        
        print(f"Running benchmark with {total_tests} test cases...")
        
        for i, test_case in enumerate(test_cases):
            # Show progress
            sys.stdout.write(f"\rTest {i+1}/{total_tests} [{(i+1)/total_tests*100:.1f}%]")
            sys.stdout.flush()
            
            try:
                result = self.run_test_case(test_case)
                self.results.append(result)
                
                # Track token usage
                test_tokens = result.get('token_usage', {})
                input_tokens = test_tokens.get('input', 0)
                output_tokens = test_tokens.get('output', 0)
                test_total_tokens = input_tokens + output_tokens
                
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_tokens += test_total_tokens
                
                # Add summary info
                summary_results.append({
                    'test_id': result['test_id'],
                    'success': result['success'],
                    'execution_time': result.get('execution_time', 0),
                    'tools_called_count': len(result.get('tools_called', [])),
                    'required_tools_count': len(result.get('required_tools', [])),
                    'optional_tools_count': len(result.get('optional_tools', [])),
                    'optional_tools_used_count': len(result.get('optional_tools_used', [])),
                    'tools_matched': result.get('required_tools_matched', False),
                    'response_matched': result.get('response_matched', False),
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': test_total_tokens,
                    'error': ''
                })
                
            except Exception as e:
                error_msg = str(e)
                self.log(f"Error in test {test_case.get('id', 'unknown')}: {error_msg}")
                
                # Add a failed result
                failed_result = {
                    'test_id': test_case.get('id', 'unknown'),
                    'prompt': test_case.get('prompt', ''),
                    'success': False,
                    'error': error_msg,
                    'token_usage': {'input': 0, 'output': 0, 'total': 0}
                }
                self.results.append(failed_result)
                
                # Add to summary
                summary_results.append({
                    'test_id': test_case.get('id', 'unknown'),
                    'success': False,
                    'execution_time': 0,
                    'tools_called_count': 0,
                    'required_tools_count': len([t for t in test_case.get('expected_tools', []) if not t.startswith('~')]),
                    'optional_tools_count': len([t for t in test_case.get('expected_tools', []) if t.startswith('~')]),
                    'optional_tools_used_count': 0,
                    'tools_matched': False,
                    'response_matched': False,
                    'input_tokens': 0,
                    'output_tokens': 0, 
                    'total_tokens': 0,
                    'error': error_msg
                })
        
        # Store total token usage for the summary
        self.overall_token_usage = {
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'total_tokens': total_tokens
        }
        
        # End progress line
        print("\nBenchmark complete!")
        
        return summary_results
    
    def print_summary(self, summary_results: List[Dict[str, Any]]) -> None:
        """Print summary statistics from the benchmark results
        
        Args:
            summary_results: List of dictionaries with benchmark results
        """
        total_tests = len(summary_results)
        successful_tests = sum(1 for r in summary_results if r['success'])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Calculate average execution time
        total_exec_time = sum(r.get('execution_time', 0) for r in summary_results)
        avg_exec_time = total_exec_time / total_tests if total_tests > 0 else 0
        
        # Calculate average token usage
        successful_results = [r for r in summary_results if r['success']]
        if successful_results:
            avg_tokens_per_success = sum(r.get('total_tokens', 0) for r in successful_results) / len(successful_results)
        else:
            avg_tokens_per_success = 0
        
        # Get overall token usage
        total_input = self.overall_token_usage.get('input_tokens', 0)
        total_output = self.overall_token_usage.get('output_tokens', 0)
        total_tokens = self.overall_token_usage.get('total_tokens', 0)
        
        print(f"\n=== BENCHMARK SUMMARY ===")
        print(f"Model: {self.model_name}")
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Success Rate: {success_rate:.2f}%")
        print(f"Average Execution Time: {avg_exec_time:.2f}s")
        
        print(f"\n=== TOKEN USAGE SUMMARY ===")
        print(f"Total Input Tokens: {total_input:,}")
        print(f"Total Output Tokens: {total_output:,}")
        print(f"Total Tokens: {total_tokens:,}")
        print(f"Average Tokens per Successful Test: {avg_tokens_per_success:.2f}")
        
        # List tests with highest token usage
        if summary_results:
            print("\nTop 3 Tests by Token Usage:")
            sorted_by_tokens = sorted(summary_results, key=lambda x: x.get('total_tokens', 0), reverse=True)[:3]
            for i, test in enumerate(sorted_by_tokens):
                print(f"  {i+1}. {test['test_id']}: {test.get('total_tokens', 0):,} tokens ({test.get('input_tokens', 0):,} input, {test.get('output_tokens', 0):,} output)")
        
        # List failed tests
        failed_tests = [r for r in summary_results if not r['success']]
        if failed_tests:
            print("\nFailed Tests:")
            for test in failed_tests:
                error_msg = test.get('error', '')
                error_detail = f": {error_msg}" if error_msg else ""
                print(f" - {test['test_id']}{error_detail}")
    
    def export_results(self, filename: str = "benchmark_results.json") -> None:
        """Export detailed benchmark results to a JSON file
        
        Args:
            filename: Output filename for the results
        """
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Detailed results exported to {filename}")
    
    def export_csv(self, summary_results: List[Dict[str, Any]], filename: str = "benchmark_results.csv") -> None:
        """Export summary results to a CSV file
        
        Args:
            summary_results: List of dictionaries with benchmark results
            filename: Output filename for the CSV
        """
        # Define CSV fields based on the first result's keys
        if not summary_results:
            print("No results to export to CSV")
            return
            
        fieldnames = list(summary_results[0].keys())
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_results)
        
        print(f"Summary results exported to {filename}")


def get_test_cases() -> List[Dict[str, Any]]:
    """Define the benchmark test cases
    
    Returns:
        List of test case dictionaries
    """
    return [
        # Basic utility tests
        {
            'id': 'weather_lookup',
            'prompt': 'What is the weather like in 94105?',
            'expected_tools': ['get_weather'],
            'expected_response_contains': ['weather', '75 F']
        },
        {
            'id': 'datetime_check',
            'prompt': 'What is today\'s date and time?',
            'expected_tools': ['get_datetime'],
            'expected_response_contains': ['date', 'time']
        },
        {
            'id': 'basic_calculation',
            'prompt': 'Calculate 24 * 7 + 365',
            'expected_tools': ['calculate'],
            'expected_response_contains': ['533']
        },
        
        # Appointment tests
        {
            'id': 'appointment_listing',
            'prompt': 'What types of appointments can I schedule?',
            'expected_tools': ['get_appointment_specialties'],
            'expected_response_contains': ['dentist', 'vision', 'hair']
        },
        {
            'id': 'dentist_availability',
            'prompt': 'I want to see a dentist. What appointments are available?',
            'expected_tools': ['~get_appointment_specialties', 'get_available_appointments'],
            'expected_response_contains': ['dentist', 'available', 'appointment']
        },

        # We expect the appointment to be booked
        {
            'id': 'book_appointment',
            'prompt': 'I\'d like to book the first available vision appointment',
            'expected_tools': ['~get_appointment_specialties', 'get_available_appointments', 'book_appointment'],
            'expected_response_contains': ['booked', 'appointment']
        },
        
        # Store locator tests
        {
            'id': 'store_types',
            'prompt': 'What types of stores can I search for?',
            'expected_tools': ['get_store_types'],
            'expected_response_contains': ['grocery', 'furniture', 'electronics']
        },
        {
            'id': 'grocery_stores',
            'prompt': 'Show me all grocery stores',
            'expected_tools': ['get_stores_by_type'],
            'expected_response_contains': ['grocery', 'store']
        },
        {
            'id': 'nearest_store_complex',
            'prompt': 'What\'s the nearest electronics store to Springfield, IL?',
            'expected_tools': ['find_nearest_store'],
            'expected_response_contains': ['electronics', 'nearest', 'Springfield']
        },
        
        # Multi-step reasoning

        # We don't expect the appointment to be booked
        {
            'id': 'complex_booking_ambiguous',
            'prompt': 'I need a haircut tomorrow afternoon and then I want to go grocery shopping nearby',
            'expected_tools': ['get_datetime', 'get_appointment_specialties', 'get_available_appointments', 'get_appointment_details', 'find_nearest_store', '~get_store_details'],
            'expected_response_contains': ['appointment', 'grocery']
        },
        {
            'id': 'complex_booking_clear',
            'prompt': 'I need a haircut tomorrow afternoon and after the appointment I want to go grocery shopping nearby',
            'expected_tools': ['get_datetime', 'get_appointment_specialties', 'get_available_appointments', 'get_appointment_details', 'find_nearest_store', '~get_store_details'],
            'expected_response_contains': ['appointment', 'grocery']
        },
        {
            'id': 'store_detail_lookup',
            'prompt': 'Tell me more about the Fresh Market store, including its hours and services',
            'expected_tools': ['get_stores_by_name', 'get_store_details'],
            'expected_response_contains': ['Fresh Market', 'hours', 'services']
        }
    ]


def main():
    """Run the benchmark tool from command line"""
    parser = argparse.ArgumentParser(description='Benchmark ToolAgent performance')
    parser.add_argument('--model', type=str, default='gemini-2.0-flash',
                        help='Model name to benchmark')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--output', '-o', type=str, default='benchmark_results',
                        help='Base filename for output files (without extension)')
    args = parser.parse_args()
    
    # Create and run benchmark
    benchmark = ToolAgentBenchmark(model_name=args.model, verbose=args.verbose)
    test_cases = get_test_cases()
    
    # Add timestamp to filename to avoid overwriting previous results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = f"{args.output}_{timestamp}"
    
    # Run the benchmark
    summary_results = benchmark.run_benchmark(test_cases)
    
    # Output results
    benchmark.print_summary(summary_results)
    benchmark.export_results(f"{output_base}.json")
    benchmark.export_csv(summary_results, f"{output_base}.csv")


if __name__ == "__main__":
    main()
