import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from openai import OpenAI
import re

def main():
    print("=== OnlineJudge Bypass with DeepSeek ===")

    # Get credentials
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Get assignment URL
    assignment_url = input("Enter assignment URL: ")

    # Get max attempts
    while True:
        try:
            max_attempts = int(input("Enter maximum number of attempts: "))
            if max_attempts > 0:
                break
            else:
                print("Please enter a positive number")
        except ValueError:
            print("Please enter a valid number")

    # Create and run scraper
    scraper = CodeJudgeScraper(username, password, assignment_url, max_attempts)
    scraper.run()

class CodeJudgeScraper:
    def __init__(self, username, password, assignment_url, max_attempts):
        self.username = username
        self.password = password
        self.assignment_url = assignment_url
        self.max_attempts = max_attempts
        self.driver = None
        self.previous_submissions = []  # Track all previous code submissions
        self.api_key = ""
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")  # Commented out for testing - remove comment to run headless
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
    def login(self):
        # Navigate to main page
        base_url = "https://oj-cds.sicc.um.edu.mo/"
        self.driver.get(base_url)
        
        # Click login button to open modal
        login_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[1]/ul/div[2]/button"))
        )
        login_button.click()
        
        # Wait for login form to appear
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[2]/div/div/div[2]/div/form"))
        )
        
        # Enter credentials
        username_input = self.driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div[2]/div/form/div[1]/div/div/input")
        password_input = self.driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div/div[2]/div/form/div[2]/div/div/input")
        
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        
        # Submit login
        submit_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[2]/div/div/div[2]/div/div/button"))
        )
        submit_button.click()
        
        # Wait for login to complete
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "/html/body/div[3]/div[2]/div/div/div[2]/div/form"))
        )
        
    def navigate_to_assignment(self):
        self.driver.get(self.assignment_url)
        # Wait for page to load using exact XPath for problem description
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[1]/div[3]")))
        
    def scrape_requirements(self):
        # Extract all text content from the webpage
        body_element = self.driver.find_element(By.TAG_NAME, "body")
        # Get all visible text from the entire page
        all_text = self.driver.execute_script("return arguments[0].innerText;", body_element)
        return f"Full webpage content:\n\n{all_text}"
        
    def scrape_results_page(self):
        # Extract all text content from the results page
        body_element = self.driver.find_element(By.TAG_NAME, "body")
        # Get all visible text from the entire results page
        all_text = self.driver.execute_script("return arguments[0].innerText;", body_element)
        return f"Full results page content:\n\n{all_text}"
        
    def extract_initial_code(self):
        # Extract any existing code from the code input area (CodeMirror editor)
        try:
            # Try to get code from CodeMirror first
            initial_code = self.driver.execute_script("""
            var codeMirrorEditors = document.querySelectorAll('.CodeMirror');
            if (codeMirrorEditors.length > 0) {
                var cm = codeMirrorEditors[0].CodeMirror;
                if (cm) {
                    return cm.getValue();
                } else {
                    // Fallback: find the hidden textarea
                    var textareas = document.querySelectorAll('textarea');
                    for (var i = 0; i < textareas.length; i++) {
                        if (textareas[i].style.display === 'none' || textareas[i].classList.contains('CodeMirror')) {
                            return textareas[i].value;
                        }
                    }
                }
            }
            // Fallback: try the old XPath approach
            var codeElement = document.evaluate('/html/body/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[2]/div/div[1]/div[2]/div/div[6]/div[1]/div/div/div/div[5]/div[1]/pre', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (codeElement) {
                return codeElement.innerText || codeElement.textContent;
            }
            return "";
            """)

            return initial_code.strip() if initial_code and initial_code.strip() else ""
        except Exception as e:
            print(f"No initial code found: {e}")
            return ""
        
    def generate_code(self, requirements, initial_code="", previous_submissions=None):
        if previous_submissions is None:
            previous_submissions = []
            
        prompt_parts = [f"Write a complete Python solution for the following coding problem:\n\n{requirements}"]
        
        if initial_code:
            prompt_parts.append(f"\nInitial code provided in the input area:\n{initial_code}")
        
        # Only include previous submissions for the first attempt
        # For subsequent attempts, the results page content will contain the submitted code
        if previous_submissions and len(previous_submissions) == 0:  # First attempt
            # No previous submissions to include for first attempt
            pass
        elif previous_submissions and len(previous_submissions) > 0:  # Subsequent attempts
            # Don't include previous submissions to save context space
            # The results page content will contain the most recent submitted code
            print(f"Optimizing context: Skipping {len(previous_submissions)} previous submissions (available in results page)")
            prompt_parts.append("\nNote: The results page content contains the previously submitted code for reference.")
        
        prompt_parts.append("\nProvide only the complete code solution, no explanations.")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            completion = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192
            )
            code = completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            print("Make sure your API key is valid and you have credits.")
            raise
        # Extract code between code blocks
        # Look for ```python ... ``` or '''python ... '''
        python_block = re.search(r'```python\s*(.*?)\s*```', code, re.DOTALL)
        if not python_block:
            python_block = re.search(r"'''python\s*(.*?)\s*'''", code, re.DOTALL)
        if not python_block:
            python_block = re.search(r'```\s*(.*?)\s*```', code, re.DOTALL)
        if python_block:
            code = python_block.group(1).strip()
        else:
            # Fallback: remove any leading/trailing markers
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.startswith("'''python"):
                code = code[10:]
            if code.startswith("'''"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            if code.endswith("'''"):
                code = code[:-3]
        return code.strip()
            
    def submit_code(self, code):
        print(f"Submitting code (length: {len(code)}): {code[:100]}...")
        
        # Handle CodeMirror editor properly
        self.driver.execute_script("""
        // Try to find CodeMirror editor first
        var codeMirrorEditors = document.querySelectorAll('.CodeMirror');
        if (codeMirrorEditors.length > 0) {
            // CodeMirror editor found
            var cm = codeMirrorEditors[0].CodeMirror;
            if (cm) {
                // Use CodeMirror API
                cm.setValue(arguments[0]);
                cm.focus();
                cm.setCursor(cm.lineCount(), 0);
                console.log('Set code using CodeMirror API');
            } else {
                // Fallback: find the hidden textarea
                var textareas = document.querySelectorAll('textarea');
                for (var i = 0; i < textareas.length; i++) {
                    if (textareas[i].style.display === 'none' || textareas[i].classList.contains('CodeMirror')) {
                        textareas[i].value = arguments[0];
                        textareas[i].dispatchEvent(new Event('input', {bubbles: true}));
                        textareas[i].dispatchEvent(new Event('change', {bubbles: true}));
                        console.log('Set code using hidden textarea');
                        break;
                    }
                }
            }
        } else {
            // Fallback for non-CodeMirror editors
            var codeElement = document.evaluate('/html/body/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[2]/div/div[1]/div[2]/div/div[6]/div[1]/div/div/div/div[5]/div[1]/pre', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (codeElement) {
                codeElement.innerHTML = arguments[0];
                codeElement.dispatchEvent(new Event('input', {bubbles: true}));
                codeElement.dispatchEvent(new Event('change', {bubbles: true}));
                console.log('Set code using XPath');
            } else {
                // Try contenteditable
                var editors = document.querySelectorAll('[contenteditable="true"]');
                if (editors.length > 0) {
                    editors[0].innerHTML = arguments[0];
                    editors[0].dispatchEvent(new Event('input', {bubbles: true}));
                    editors[0].dispatchEvent(new Event('change', {bubbles: true}));
                    console.log('Set code using contenteditable');
                } else {
                    // Try textarea
                    var textareas = document.querySelectorAll('textarea');
                    if (textareas.length > 0) {
                        textareas[0].value = arguments[0];
                        textareas[0].dispatchEvent(new Event('input', {bubbles: true}));
                        textareas[0].dispatchEvent(new Event('change', {bubbles: true}));
                        console.log('Set code using textarea');
                    }
                }
            }
        }
        """, code)

        # Wait a moment for the code to be set
        time.sleep(1)
        
        # Verify the code was set correctly
        verification_code = self.driver.execute_script("""
        var codeMirrorEditors = document.querySelectorAll('.CodeMirror');
        if (codeMirrorEditors.length > 0) {
            var cm = codeMirrorEditors[0].CodeMirror;
            if (cm) {
                return cm.getValue();
            } else {
                var textareas = document.querySelectorAll('textarea');
                for (var i = 0; i < textareas.length; i++) {
                    if (textareas[i].style.display === 'none' || textareas[i].classList.contains('CodeMirror')) {
                        return textareas[i].value;
                    }
                }
            }
        }
        return "";
        """)
        
        print(f"Verification - Code in editor (length: {len(verification_code)}): {verification_code[:100]}...")
        
        if verification_code.strip() != code.strip():
            print("WARNING: Code in editor doesn't match the code we tried to set!")
        else:
            print("✓ Code successfully set in editor")

        # Submit using the correct XPath from the HTML
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'ivu-btn-warning') and contains(., 'Submit')]")
        submit_button.click()
        print("Clicked submit button")        # Wait for evaluation to complete
        time.sleep(10)
        
        # Wait for result using exact XPath
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[2]/div/div[2]/div[1]/div/div")))
        
    def check_result(self):
        # Click the button to go to detailed results
        result_button = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[2]/div/div[2]/div[1]/div/div")
        result_button.click()
        
        # Wait for results page to load
        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table")))
        except TimeoutException:
            print("Table not found; waiting for tbody...")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, "//tbody[@class='ivu-table-tbody']")))
        
        # Scrape the entire webpage content from results page
        results_page_content = self.scrape_results_page()
        print(f"Scraped full results page content (length: {len(results_page_content)})")
        
        # Get overall status
        try:
            overall_status_elem = self.driver.find_element(By.XPATH, "//span[@class='title']")
            overall_status = overall_status_elem.text
        except:
            overall_status = "Unknown"
        
        # Parse detailed test case results
        test_results = []
        table_rows = self.driver.find_elements(By.XPATH, "//tbody[@class='ivu-table-tbody']/tr")
        
        for row in table_rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 5:
                    test_id = cells[0].text.strip()
                    status_elem = cells[1].find_element(By.XPATH, ".//span[@class='ivu-tag-text']")
                    status = status_elem.text.strip()
                    memory = cells[2].text.strip()
                    time_taken = cells[3].text.strip()
                    score = cells[4].text.strip()
                    
                    test_results.append({
                        'id': test_id,
                        'status': status,
                        'memory': memory,
                        'time': time_taken,
                        'score': score
                    })
            except Exception as e:
                continue
        
        # Get submitted code if available
        submitted_code = ""
        try:
            # Try multiple selectors for the submitted code
            code_selectors = [
                "//pre[@data-v-42d1f142]/code",
                "//pre[contains(@class, 'CodeMirror-line')]",
                "//div[contains(@class, 'CodeMirror-code')]//pre",
                "//code"
            ]
            
            for selector in code_selectors:
                try:
                    code_elem = self.driver.find_element(By.XPATH, selector)
                    submitted_code = code_elem.text.strip()
                    if submitted_code:
                        break
                except:
                    continue
                    
            print(f"Extracted submitted code (length: {len(submitted_code)}): {submitted_code[:100]}...")
            
        except Exception as e:
            print(f"Could not extract submitted code: {e}")
            pass
        
        # Go back to assignment page
        self.driver.get(self.assignment_url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/div[1]/div[1]/div/div[1]/div[1]/div[3]")))
        
        # Analyze results
        accepted_count = sum(1 for test in test_results if test['status'].lower() == 'accepted')
        wrong_count = sum(1 for test in test_results if 'wrong answer' in test['status'].lower())
        total_tests = len(test_results)
        
        # Create detailed feedback
        feedback_parts = []
        feedback_parts.append(f"Overall Status: {overall_status}")
        feedback_parts.append(f"Test Results: {accepted_count}/{total_tests} tests passed")
        
        if accepted_count == total_tests and total_tests > 0:
            status = "accepted"
            feedback_parts.append("✅ All tests passed!")
        elif accepted_count > 0:
            status = "partial"
            feedback_parts.append(f"⚠️  Partial success: {accepted_count} tests passed, {wrong_count} failed")
            
            # List failed test cases
            failed_tests = [test for test in test_results if 'wrong answer' in test['status'].lower()]
            if failed_tests:
                feedback_parts.append("\nFailed test cases:")
                for test in failed_tests[:5]:  # Show first 5 failures
                    feedback_parts.append(f"  • Test {test['id']}: {test['status']} (Memory: {test['memory']}, Time: {test['time']})")
            
            # List passed test cases
            passed_tests = [test for test in test_results if test['status'].lower() == 'accepted']
            if passed_tests:
                feedback_parts.append("\nPassed test cases:")
                for test in passed_tests:
                    feedback_parts.append(f"  • Test {test['id']}: {test['status']} (Memory: {test['memory']}, Time: {test['time']})")
        
        else:
            status = "denied"
            feedback_parts.append("❌ All tests failed")
            feedback_parts.append("\nFailed test cases:")
            for test in test_results[:5]:  # Show first 5 failures
                feedback_parts.append(f"  • Test {test['id']}: {test['status']} (Memory: {test['memory']}, Time: {test['time']})")
        
        # Add submitted code if available
        if submitted_code:
            feedback_parts.append(f"\nSubmitted Code:\n{submitted_code}")
        
        # Add full results page content for comprehensive context
        if results_page_content:
            feedback_parts.append(f"\n{results_page_content}")
        
        detailed_feedback = "\n".join(feedback_parts)
        return status, detailed_feedback
            
    def analyze_feedback(self, feedback):
        # Enhanced analysis based on detailed feedback
        if not feedback:
            return "unknown"

        feedback_lower = feedback.lower()

        # Check for complete success
        if "all tests passed" in feedback_lower or "accepted" in feedback_lower:
            return "accepted"

        # Check for partial success
        if "partial success" in feedback_lower or "partial accepted" in feedback_lower:
            return "partial"

        # Check for complete failure
        if "all tests failed" in feedback_lower or "0/" in feedback_lower:
            return "wrong"

        # Check for timeout issues
        if "time limit" in feedback_lower or "timeout" in feedback_lower:
            return "timeout"

        # Check for memory issues
        if "memory limit" in feedback_lower or "out of memory" in feedback_lower:
            return "memory"

        return "unknown"
            
    def rewrite_code(self, original_code, requirements, feedback_type, detailed_feedback="", initial_code="", previous_submissions=None):
        if previous_submissions is None:
            previous_submissions = []
            
        # Enhanced prompts based on detailed feedback
        base_prompt_parts = [f"Original code:\n{original_code}"]
        
        if detailed_feedback:
            base_prompt_parts.append(f"\nDetailed Feedback: {detailed_feedback}")
        
        base_prompt_parts.append(f"\nRequirements: {requirements}")
        
        if initial_code:
            base_prompt_parts.append(f"\nInitial code provided: {initial_code}")
        
        # Don't include previous submissions to save context space
        # The results page content in detailed_feedback already contains the submitted code
        if previous_submissions and len(previous_submissions) > 0:
            print(f"Optimizing context: Previous submissions ({len(previous_submissions)}) available in results page content")
            base_prompt_parts.append(f"\nNote: Previous submission attempts are available in the results page content above.")
        
        base_prompt = "\n".join(base_prompt_parts)
        
        if feedback_type == "timeout":
            prompt = f"The following code exceeded time limit. Optimize it for better performance:\n\n{base_prompt}\n\nPlease provide an optimized version that runs faster."
        elif feedback_type == "wrong":
            prompt = f"The following code is incorrect and failed all tests. Fix the logic errors:\n\n{base_prompt}\n\nAnalyze the failed test cases and provide a corrected version."
        elif feedback_type == "partial":
            prompt = f"The following code passed some tests but failed others. Improve it to pass all tests:\n\n{base_prompt}\n\nFocus on fixing the logic for the failed test cases while maintaining the correct behavior for passed tests."
        elif feedback_type == "memory":
            prompt = f"The following code exceeded memory limits. Optimize memory usage:\n\n{base_prompt}\n\nPlease provide a more memory-efficient version."
        else:
            prompt = f"Improve the following code based on the feedback:\n\n{base_prompt}\n\nPlease provide an improved version."
            
        try:
            completion = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=8192
            )
            code = completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            print("Make sure your API key is valid and you have credits.")
            raise
        # Extract code between code blocks
        # Look for ```python ... ``` or '''python ... '''
        python_block = re.search(r'```python\s*(.*?)\s*```', code, re.DOTALL)
        if not python_block:
            python_block = re.search(r"'''python\s*(.*?)\s*'''", code, re.DOTALL)
        if not python_block:
            python_block = re.search(r'```\s*(.*?)\s*```', code, re.DOTALL)
        if python_block:
            code = python_block.group(1).strip()
        else:
            # Fallback: remove any leading/trailing markers
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.startswith("'''python"):
                code = code[10:]
            if code.startswith("'''"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            if code.endswith("'''"):
                code = code[:-3]
        return code.strip()
            
    def run(self):
        self.setup_driver()
        
        try:
            self.login()
            self.navigate_to_assignment()
            
            requirements = self.scrape_requirements()
            print(f"Scraped requirements: {requirements[:200]}...")
            
            initial_code = self.extract_initial_code()
            if initial_code:
                print(f"Found initial code: {initial_code[:100]}...")
            else:
                print("No initial code found")
            
            code = self.generate_code(requirements, initial_code, self.previous_submissions)
            print("Generated initial code")
            print(f"Generated code length: {len(code)}")
            print(f"Generated code preview: {code[:200]}...")
            
            for attempt in range(self.max_attempts):
                print(f"\n--- Attempt {attempt + 1}/{self.max_attempts} ---")
                
                self.submit_code(code)
                # Store this submission for future context
                self.previous_submissions.append(code)
                
                status, feedback = self.check_result()
                
                print(f"Submission result: {status}")
                
                if status == "accepted":
                    print("🎉 Solution accepted!")
                    break
                elif status == "partial":
                    print("⚠️  Partial acceptance - may need manual review")
                    break
                else:
                    feedback_type = self.analyze_feedback(feedback)
                    print(f"Feedback type: {feedback_type}")
                    print(f"Detailed feedback: {feedback[:500]}...")
                    
                    code = self.rewrite_code(code, requirements, feedback_type, feedback, initial_code, self.previous_submissions)
                    print("Rewrote code based on feedback")
                    
                time.sleep(5)  # Wait between submissions
                
            print(f"\nProcess completed after {min(attempt + 1, self.max_attempts)} attempts.")
                
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    main()