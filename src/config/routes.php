<?php

/**
 * Route Configuration
 *
 * Define all application routes here.
 *
 * Route Format (Phase 4 - With Middleware):
 * [HTTP_METHOD, '/url/pattern', 'ControllerName@actionMethod', ['middleware' => [...]]]
 *
 * Example:
 * ['GET', '/', 'HomeController@index']
 * ['GET', '/about', 'HomeController@about']
 * ['GET', '/users/{id}', 'UserController@show']
 * ['POST', '/users', 'UserController@store', ['middleware' => ['CsrfMiddleware']]]
 *
 * @package ADA Framework
 * @version 1.0 (Phase 4)
 */

return [
    // Global middleware (runs on all routes)
    'middleware' => [
        'SessionMiddleware',
    ],

    // Routes
    'routes' => [
        // Home routes
        ['GET', '/', 'HomeController@index'],
        ['GET', '/about', 'HomeController@about'],
        ['GET', '/contact', 'HomeController@contact'],
        ['POST', '/contact', 'HomeController@submitContact'],

        // Devoir routes (Phase 2 - Database demonstration)
        ['GET', '/devoirs', 'DevoirController@index'],
        ['GET', '/devoirs/show', 'DevoirController@show'],
        ['GET', '/devoirs/upcoming', 'DevoirController@upcoming'],

        // Test route with parameter (for future implementation)
        // ['GET', '/hello/{name}', 'HomeController@hello'],
    ],
];
