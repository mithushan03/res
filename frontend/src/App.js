import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';
import { Separator } from './components/ui/separator';
import { GraduationCap, BookOpen, Trophy, User, LogOut, AlertCircle, CheckCircle } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('login');

  // Login/Register states
  const [loginData, setLoginData] = useState({ student_id: '', password: '' });
  const [registerData, setRegisterData] = useState({
    student_id: '',
    name: '',
    email: '',
    password: '',
    role: 'student'
  });

  // Results state
  const [results, setResults] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [students, setStudents] = useState([]);
  const [newResult, setNewResult] = useState({
    student_id: '',
    subject_id: '',
    marks: '',
    semester: '',
    year: ''
  });

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      fetchSubjects();
      if (user.role === 'student') {
        fetchStudentResults(user.student_id);
      } else if (user.role === 'admin') {
        fetchStudents();
      }
    }
  }, [user]);

  const showMessage = (message, type = 'error') => {
    if (type === 'error') {
      setError(message);
      setSuccess('');
    } else {
      setSuccess(message);
      setError('');
    }
    setTimeout(() => {
      setError('');
      setSuccess('');
    }, 5000);
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
      localStorage.removeItem('token');
      setToken(null);
    }
  };

  const fetchSubjects = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/subjects`);
      if (response.ok) {
        const data = await response.json();
        setSubjects(data.subjects);
      }
    } catch (error) {
      console.error('Error fetching subjects:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/students`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStudents(data.students);
      }
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const fetchStudentResults = async (studentId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/results/student/${studentId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        showMessage('Failed to fetch results');
      }
    } catch (error) {
      console.error('Error fetching results:', error);
      showMessage('Error fetching results');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      });

      const data = await response.json();

      if (response.ok) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        showMessage('Login successful!', 'success');
      } else {
        showMessage(data.detail || 'Login failed');
      }
    } catch (error) {
      showMessage('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerData)
      });

      const data = await response.json();

      if (response.ok) {
        showMessage('Registration successful! Please login.', 'success');
        setActiveTab('login');
        setRegisterData({ student_id: '', name: '', email: '', password: '', role: 'student' });
      } else {
        showMessage(data.detail || 'Registration failed');
      }
    } catch (error) {
      showMessage('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddResult = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/results`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...newResult,
          marks: parseFloat(newResult.marks)
        })
      });

      const data = await response.json();

      if (response.ok) {
        showMessage('Result added successfully!', 'success');
        setNewResult({ student_id: '', subject_id: '', marks: '', semester: '', year: '' });
        fetchStudentResults(newResult.student_id);
      } else {
        showMessage(data.detail || 'Failed to add result');
      }
    } catch (error) {
      showMessage('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setResults(null);
    localStorage.removeItem('token');
    showMessage('Logged out successfully!', 'success');
  };

  const getGradeColor = (grade) => {
    const colors = {
      'A+': 'bg-green-500',
      'A': 'bg-green-400',
      'B+': 'bg-blue-500',
      'B': 'bg-blue-400',
      'C+': 'bg-yellow-500',
      'C': 'bg-yellow-400',
      'F': 'bg-red-500'
    };
    return colors[grade] || 'bg-gray-400';
  };

  // Authentication UI
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <GraduationCap className="h-12 w-12 text-indigo-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">Smart Student Results</h1>
            </div>
            <p className="text-lg text-gray-600">Academic Performance Management System</p>
          </div>

          {(error || success) && (
            <div className="max-w-md mx-auto mb-6">
              <Alert className={success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
                {success ? <CheckCircle className="h-4 w-4 text-green-600" /> : <AlertCircle className="h-4 w-4 text-red-600" />}
                <AlertDescription className={success ? "text-green-800" : "text-red-800"}>
                  {error || success}
                </AlertDescription>
              </Alert>
            </div>
          )}

          <div className="max-w-md mx-auto">
            <Card className="shadow-xl border-0">
              <CardHeader className="text-center pb-2">
                <CardTitle className="text-2xl">Welcome</CardTitle>
                <CardDescription>Access your academic results</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-2 mb-6">
                    <TabsTrigger value="login">Login</TabsTrigger>
                    <TabsTrigger value="register">Register</TabsTrigger>
                  </TabsList>

                  <TabsContent value="login">
                    <form onSubmit={handleLogin} className="space-y-4">
                      <div>
                        <Label htmlFor="student_id">Student ID</Label>
                        <Input
                          id="student_id"
                          type="text"
                          placeholder="Enter your Student ID"
                          value={loginData.student_id}
                          onChange={(e) => setLoginData({...loginData, student_id: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="password">Password</Label>
                        <Input
                          id="password"
                          type="password"
                          placeholder="Enter your password"
                          value={loginData.password}
                          onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                      </Button>
                    </form>
                  </TabsContent>

                  <TabsContent value="register">
                    <form onSubmit={handleRegister} className="space-y-4">
                      <div>
                        <Label htmlFor="reg_student_id">Student ID</Label>
                        <Input
                          id="reg_student_id"
                          type="text"
                          placeholder="Enter Student ID"
                          value={registerData.student_id}
                          onChange={(e) => setRegisterData({...registerData, student_id: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="name">Full Name</Label>
                        <Input
                          id="name"
                          type="text"
                          placeholder="Enter your full name"
                          value={registerData.name}
                          onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          placeholder="Enter your email"
                          value={registerData.email}
                          onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="reg_password">Password</Label>
                        <Input
                          id="reg_password"
                          type="password"
                          placeholder="Create a password"
                          value={registerData.password}
                          onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? 'Registering...' : 'Register'}
                      </Button>
                    </form>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // Main Application UI
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <GraduationCap className="h-8 w-8 text-indigo-600 mr-3" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Student Results Portal</h1>
                <p className="text-sm text-gray-600">Welcome, {user.name}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="secondary" className="capitalize">
                <User className="h-3 w-3 mr-1" />
                {user.role}
              </Badge>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {(error || success) && (
          <div className="mb-6">
            <Alert className={success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
              {success ? <CheckCircle className="h-4 w-4 text-green-600" /> : <AlertCircle className="h-4 w-4 text-red-600" />}
              <AlertDescription className={success ? "text-green-800" : "text-red-800"}>
                {error || success}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Student Dashboard */}
        {user.role === 'student' && results && (
          <div className="space-y-6">
            {/* Student Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Trophy className="h-5 w-5 mr-2 text-yellow-500" />
                  Academic Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-indigo-600">{results.overall_gpa}</div>
                    <div className="text-sm text-gray-600">Overall GPA</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">{results.total_subjects}</div>
                    <div className="text-sm text-gray-600">Total Subjects</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{Object.keys(results.results_by_semester).length}</div>
                    <div className="text-sm text-gray-600">Semesters</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Semester Results */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <BookOpen className="h-6 w-6 mr-2" />
                Semester-wise Results
              </h2>
              
              {Object.entries(results.results_by_semester).map(([semesterKey, semesterResults]) => (
                <Card key={semesterKey}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="capitalize">
                        {semesterKey.replace('-', ' - ')}
                      </CardTitle>
                      <Badge variant="outline" className="text-lg font-semibold">
                        GPA: {results.semester_gpas[semesterKey]}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4">
                      {semesterResults.map((result) => (
                        <div key={result.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900">{result.subject_name}</h4>
                            <p className="text-sm text-gray-600">
                              {result.marks}/{result.max_marks} marks
                            </p>
                          </div>
                          <Badge className={`${getGradeColor(result.grade)} text-white`}>
                            {result.grade}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Admin Dashboard */}
        {user.role === 'admin' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Add Student Result</CardTitle>
                <CardDescription>Enter marks for a student</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAddResult} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="student_select">Student</Label>
                      <select
                        id="student_select"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        value={newResult.student_id}
                        onChange={(e) => setNewResult({...newResult, student_id: e.target.value})}
                        required
                      >
                        <option value="">Select Student</option>
                        {students.map((student) => (
                          <option key={student.id} value={student.student_id}>
                            {student.name} ({student.student_id})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="subject_select">Subject</Label>
                      <select
                        id="subject_select"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        value={newResult.subject_id}
                        onChange={(e) => setNewResult({...newResult, subject_id: e.target.value})}
                        required
                      >
                        <option value="">Select Subject</option>
                        {subjects.map((subject) => (
                          <option key={subject.id} value={subject.id}>
                            {subject.name} ({subject.code})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="marks">Marks</Label>
                      <Input
                        id="marks"
                        type="number"
                        placeholder="Enter marks"
                        value={newResult.marks}
                        onChange={(e) => setNewResult({...newResult, marks: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="semester">Semester</Label>
                      <Input
                        id="semester"
                        type="text"
                        placeholder="e.g., Fall, Spring"
                        value={newResult.semester}
                        onChange={(e) => setNewResult({...newResult, semester: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="year">Year</Label>
                      <Input
                        id="year"
                        type="text"
                        placeholder="e.g., 2024"
                        value={newResult.year}
                        onChange={(e) => setNewResult({...newResult, year: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Adding...' : 'Add Result'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;