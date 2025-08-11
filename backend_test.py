import requests
import sys
import json
from datetime import datetime

class StudentResultAPITester:
    def __init__(self, base_url="https://294c4a5e-93ba-4393-8f51-ac5284762580.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.student_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.subject_ids = {}
        self.student_ids = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/auth/login",
            200,
            data={"student_id": "ADMIN001", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_student_login(self):
        """Test student login"""
        success, response = self.run_test(
            "Student Login",
            "POST",
            "api/auth/login",
            200,
            data={"student_id": "ST001", "password": "student123"}
        )
        if success and 'access_token' in response:
            self.student_token = response['access_token']
            print(f"   Student token obtained: {self.student_token[:20]}...")
            return True
        return False

    def test_invalid_login(self):
        """Test invalid login credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "api/auth/login",
            401,
            data={"student_id": "INVALID", "password": "wrong"}
        )
        return success

    def test_get_current_user_admin(self):
        """Test getting current user info for admin"""
        success, response = self.run_test(
            "Get Current User (Admin)",
            "GET",
            "api/auth/me",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Admin user: {response.get('name', 'N/A')} ({response.get('role', 'N/A')})")
        return success

    def test_get_current_user_student(self):
        """Test getting current user info for student"""
        success, response = self.run_test(
            "Get Current User (Student)",
            "GET",
            "api/auth/me",
            200,
            token=self.student_token
        )
        if success:
            print(f"   Student user: {response.get('name', 'N/A')} ({response.get('role', 'N/A')})")
        return success

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        success, response = self.run_test(
            "Unauthorized Access",
            "GET",
            "api/auth/me",
            401
        )
        return success

    def test_get_subjects(self):
        """Test getting all subjects"""
        success, response = self.run_test(
            "Get Subjects",
            "GET",
            "api/subjects",
            200
        )
        if success and 'subjects' in response:
            subjects = response['subjects']
            print(f"   Found {len(subjects)} subjects")
            for subject in subjects:
                self.subject_ids[subject['code']] = subject['id']
                print(f"   - {subject['name']} ({subject['code']})")
        return success

    def test_create_subject_admin(self):
        """Test creating a subject as admin"""
        test_subject = {
            "name": "Test Subject",
            "code": "TEST101",
            "credits": 3
        }
        success, response = self.run_test(
            "Create Subject (Admin)",
            "POST",
            "api/subjects",
            200,
            data=test_subject,
            token=self.admin_token
        )
        return success

    def test_create_subject_student_forbidden(self):
        """Test creating a subject as student (should fail)"""
        test_subject = {
            "name": "Forbidden Subject",
            "code": "FORB101",
            "credits": 3
        }
        success, response = self.run_test(
            "Create Subject (Student - Forbidden)",
            "POST",
            "api/subjects",
            403,
            data=test_subject,
            token=self.student_token
        )
        return success

    def test_get_students_admin(self):
        """Test getting all students as admin"""
        success, response = self.run_test(
            "Get Students (Admin)",
            "GET",
            "api/students",
            200,
            token=self.admin_token
        )
        if success and 'students' in response:
            students = response['students']
            print(f"   Found {len(students)} students")
            for student in students:
                self.student_ids[student['student_id']] = student['id']
                print(f"   - {student['name']} ({student['student_id']})")
        return success

    def test_get_students_student_forbidden(self):
        """Test getting students as student (should fail)"""
        success, response = self.run_test(
            "Get Students (Student - Forbidden)",
            "GET",
            "api/students",
            403,
            token=self.student_token
        )
        return success

    def test_add_result_admin(self):
        """Test adding a result as admin"""
        if not self.subject_ids:
            print("   Skipping - No subjects available")
            return False
            
        # Use first available subject
        subject_id = list(self.subject_ids.values())[0]
        result_data = {
            "student_id": "ST001",
            "subject_id": subject_id,
            "marks": 85.0,
            "semester": "Fall",
            "year": "2024"
        }
        success, response = self.run_test(
            "Add Result (Admin)",
            "POST",
            "api/results",
            200,
            data=result_data,
            token=self.admin_token
        )
        if success:
            print(f"   Result added with grade: {response.get('result', {}).get('grade', 'N/A')}")
        return success

    def test_add_result_student_forbidden(self):
        """Test adding a result as student (should fail)"""
        if not self.subject_ids:
            print("   Skipping - No subjects available")
            return False
            
        subject_id = list(self.subject_ids.values())[0]
        result_data = {
            "student_id": "ST001",
            "subject_id": subject_id,
            "marks": 90.0,
            "semester": "Spring",
            "year": "2024"
        }
        success, response = self.run_test(
            "Add Result (Student - Forbidden)",
            "POST",
            "api/results",
            403,
            data=result_data,
            token=self.student_token
        )
        return success

    def test_get_student_results_own(self):
        """Test student getting their own results"""
        success, response = self.run_test(
            "Get Own Results (Student)",
            "GET",
            "api/results/student/ST001",
            200,
            token=self.student_token
        )
        if success:
            print(f"   Overall GPA: {response.get('overall_gpa', 'N/A')}")
            print(f"   Total subjects: {response.get('total_subjects', 'N/A')}")
            print(f"   Semesters: {len(response.get('results_by_semester', {}))}")
        return success

    def test_get_student_results_other_forbidden(self):
        """Test student getting another student's results (should fail)"""
        success, response = self.run_test(
            "Get Other Results (Student - Forbidden)",
            "GET",
            "api/results/student/ST002",
            403,
            token=self.student_token
        )
        return success

    def test_get_student_results_admin(self):
        """Test admin getting student results"""
        success, response = self.run_test(
            "Get Student Results (Admin)",
            "GET",
            "api/results/student/ST001",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Overall GPA: {response.get('overall_gpa', 'N/A')}")
            print(f"   Total subjects: {response.get('total_subjects', 'N/A')}")
        return success

    def test_results_summary_admin(self):
        """Test getting results summary as admin"""
        success, response = self.run_test(
            "Results Summary (Admin)",
            "GET",
            "api/results/summary",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Total students: {response.get('total_students', 'N/A')}")
            print(f"   Total subjects: {response.get('total_subjects', 'N/A')}")
            print(f"   Total results: {response.get('total_results', 'N/A')}")
        return success

    def test_results_summary_student_forbidden(self):
        """Test getting results summary as student (should fail)"""
        success, response = self.run_test(
            "Results Summary (Student - Forbidden)",
            "GET",
            "api/results/summary",
            403,
            token=self.student_token
        )
        return success

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user = {
            "student_id": f"TEST{timestamp}",
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "testpass123",
            "role": "student"
        }
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/auth/register",
            200,
            data=test_user
        )
        if success:
            print(f"   Registered user: {response.get('user', {}).get('name', 'N/A')}")
        return success

    def test_duplicate_registration(self):
        """Test duplicate user registration (should fail)"""
        duplicate_user = {
            "student_id": "ST001",  # This should already exist
            "name": "Duplicate User",
            "email": "duplicate@example.com",
            "password": "testpass123",
            "role": "student"
        }
        success, response = self.run_test(
            "Duplicate Registration",
            "POST",
            "api/auth/register",
            400,
            data=duplicate_user
        )
        return success

def main():
    print("🚀 Starting Smart Student Result Management System API Tests")
    print("=" * 60)
    
    tester = StudentResultAPITester()
    
    # Test sequence
    tests = [
        # Basic connectivity
        tester.test_health_check,
        
        # Authentication tests
        tester.test_admin_login,
        tester.test_student_login,
        tester.test_invalid_login,
        tester.test_get_current_user_admin,
        tester.test_get_current_user_student,
        tester.test_unauthorized_access,
        
        # Registration tests
        tester.test_user_registration,
        tester.test_duplicate_registration,
        
        # Subject tests
        tester.test_get_subjects,
        tester.test_create_subject_admin,
        tester.test_create_subject_student_forbidden,
        
        # Student management tests
        tester.test_get_students_admin,
        tester.test_get_students_student_forbidden,
        
        # Results tests
        tester.test_add_result_admin,
        tester.test_add_result_student_forbidden,
        tester.test_get_student_results_own,
        tester.test_get_student_results_other_forbidden,
        tester.test_get_student_results_admin,
        
        # Summary tests
        tester.test_results_summary_admin,
        tester.test_results_summary_student_forbidden,
    ]
    
    # Run all tests
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())