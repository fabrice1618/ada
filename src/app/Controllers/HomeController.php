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
     * @return void
     */
    public function index()
    {
        $data = [
            'title' => 'Welcome to ADA Framework',
            'heading' => 'Hello from the ADA Framework!',
            'message' => 'This is a lightweight PHP MVC framework with zero dependencies.',
            'version' => '1.0 (Phase 1)',
            'features' => [
                'MVC Architecture',
                'Simple Routing',
                'Template Engine',
                'Security Features (Coming Soon)',
                'Database Layer (Coming Soon)',
            ]
        ];

        $this->view('home/index', $data);
    }

    /**
     * Display the about page
     *
     * @return void
     */
    public function about()
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

        $this->view('home/about', $data);
    }

    /**
     * Display the contact page
     *
     * @return void
     */
    public function contact()
    {
        $data = [
            'title' => 'Contact Us',
            'heading' => 'Get in Touch',
            'message' => 'This is a demo contact page. Form functionality will be added in Phase 3.',
        ];

        $this->view('home/contact', $data);
    }
}
