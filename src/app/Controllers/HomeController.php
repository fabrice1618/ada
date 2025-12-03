<?php

/**
 * Home Controller
 *
 * Handles main pages of the application (home, about, contact).
 *
 * @package ADA Framework
 * @version 1.0 (Phase 1)
 */
class HomeController extends Controller
{
    /**
     * Display the homepage
     *
     * @param Request $request
     * @return Response
     */
    public function index(Request $request)
    {
        // Load User model to demonstrate database integration
        require_once __DIR__ . '/../Models/User.php';
        require_once __DIR__ . '/../Models/Devoir.php';

        $userModel = new User();
        $devoirModel = new Devoir();

        // Get statistics from database
        $userCount = $userModel->count();
        $devoirCount = $devoirModel->count();
        $upcomingDevoirs = $devoirModel->getUpcoming();

        $data = [
            'title' => 'Welcome to ADA Framework',
            'heading' => 'Hello from the ADA Framework!',
            'message' => 'This is a lightweight PHP MVC framework with zero dependencies.',
            'version' => '3.0 (Phase 3 - Security Foundation)',
            'features' => [
                'MVC Architecture',
                'Simple Routing',
                'Template Engine',
                'Database Layer with PDO',
                'Base Model with CRUD Operations',
                'CSRF Protection',
                'XSS Prevention',
                'Secure Session Management',
                'Input Sanitization & Validation',
            ],
            'stats' => [
                'users' => $userCount,
                'devoirs' => $devoirCount,
                'upcoming' => count($upcomingDevoirs)
            ]
        ];

        return $this->view('home/index', $data);
    }

    /**
     * Display the about page
     *
     * @param Request $request
     * @return Response
     */
    public function about(Request $request)
    {
        $data = [
            'title' => 'About ADA Framework',
            'heading' => 'About ADA',
            'description' => 'ADA is a PHP micro framework built with security and simplicity in mind.',
            'principles' => [
                'Zero Dependencies' => 'Pure PHP implementation with no third-party libraries',
                'Security First' => 'Built-in protection against XSS, CSRF, and SQL injection',
                'Developer Friendly' => 'Intuitive API with minimal learning curve',
                'Performance' => 'Lightweight with low overhead',
            ]
        ];

        return $this->view('home/about', $data);
    }

    /**
     * Display the contact page
     *
     * @param Request $request
     * @return Response
     */
    public function contact(Request $request)
    {
        $data = [
            'title' => 'Contact Us',
            'heading' => 'Get in Touch',
            'message' => 'Send us a message using the form below.',
        ];

        return $this->view('home/contact', $data);
    }

    /**
     * Handle contact form submission
     *
     * @param Request $request
     * @return Response
     */
    public function submitContact(Request $request)
    {
        // Sanitize input data
        $name = Security::sanitize($request->post('name', ''), true);
        $email = Security::sanitize($request->post('email', ''), true);
        $message = Security::sanitize($request->post('message', ''), true);

        // Basic validation
        $errors = [];

        if (empty($name)) {
            $errors['name'] = 'Name is required';
        }

        if (empty($email)) {
            $errors['email'] = 'Email is required';
        } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $errors['email'] = 'Please provide a valid email address';
        }

        if (empty($message)) {
            $errors['message'] = 'Message is required';
        }

        // If validation fails, redirect back with errors and old input
        if (!empty($errors)) {
            Session::flash('_errors', $errors);
            Session::flash('_old_input', $request->post());
            return $this->redirect('/contact');
        }

        // Process the form (in a real app, this would save to database or send email)
        // For now, we'll just show a success message

        Session::flash('success', "Thank you, {$name}! Your message has been received. We'll get back to you at {$email} soon.");
        return $this->redirect('/contact');
    }
}
