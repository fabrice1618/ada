<?php

/**
 * Devoir Controller
 *
 * Handles assignment (devoir) related requests
 */
class DevoirController extends Controller
{
    /**
     * Devoir model instance
     *
     * @var Devoir
     */
    private Devoir $devoirModel;

    /**
     * Depose model instance
     *
     * @var Depose
     */
    private Depose $deposeModel;

    /**
     * Constructor - initialize models
     */
    public function __construct()
    {
        // Load models
        require_once __DIR__ . '/../Models/Devoir.php';
        require_once __DIR__ . '/../Models/Depose.php';

        $this->devoirModel = new Devoir();
        $this->deposeModel = new Depose();
    }

    /**
     * List all devoirs
     *
     * @param Request $request
     * @return Response
     */
    public function index(Request $request)
    {
        $devoirs = $this->devoirModel->all();

        // Add submission count for each devoir
        foreach ($devoirs as &$devoir) {
            $devoir['submission_count'] = $this->deposeModel->countByDevoir($devoir['iddevoirs']);
        }

        return $this->view('devoirs/index', [
            'title' => 'All Assignments',
            'devoirs' => $devoirs
        ]);
    }

    /**
     * Show a specific devoir with its submissions
     *
     * @param Request $request
     * @return Response
     */
    public function show(Request $request)
    {
        // For now, we'll show the first devoir as an example
        // In Phase 4+, we'll get the ID from route parameters
        $devoir = $this->devoirModel->first();

        if (!$devoir) {
            return new Response("<h1>No assignment found</h1>", 404);
        }

        $submissions = $this->deposeModel->getByDevoir($devoir['iddevoirs']);

        return $this->view('devoirs/show', [
            'title' => 'Assignment: ' . $devoir['shortcode'],
            'devoir' => $devoir,
            'submissions' => $submissions,
            'isOpen' => $this->devoirModel->isOpen($devoir['iddevoirs'])
        ]);
    }

    /**
     * Display upcoming assignments
     *
     * @param Request $request
     * @return Response
     */
    public function upcoming(Request $request)
    {
        $devoirs = $this->devoirModel->getUpcoming();

        return $this->view('devoirs/upcoming', [
            'title' => 'Upcoming Assignments',
            'devoirs' => $devoirs
        ]);
    }
}
