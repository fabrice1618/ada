<?php

/**
 * Route Configuration
 *
 * Define all application routes here.
 *
 * Route Format:
 * [HTTP_METHOD, '/url/pattern', 'ControllerName@actionMethod']
 *
 * Example:
 * ['GET', '/', 'HomeController@index']
 * ['GET', '/about', 'HomeController@about']
 * ['GET', '/users/{id}', 'UserController@show']
 * ['POST', '/users', 'UserController@store']
 *
 * @package ADA Framework
 * @version 1.0 (Phase 1)
 */

return [
    // Home routes
    ['GET', '/', 'HomeController@index'],
    ['GET', '/about', 'HomeController@about'],
    ['GET', '/contact', 'HomeController@contact'],

    // Test route with parameter (for future implementation)
    // ['GET', '/hello/{name}', 'HomeController@hello'],
];
