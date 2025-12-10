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

    /**
     * Display submission form for a specific devoir
     *
     * @param Request $request
     * @param string $shortcode Devoir shortcode from URL
     * @return Response
     */
    public function deposeForm(Request $request, string $shortcode)
    {
        // Find devoir by shortcode
        $devoir = $this->devoirModel->findByShortcode($shortcode);

        // Check if devoir exists
        if (!$devoir) {
            return $this->view('deposes/closed', [
                'title' => 'Devoir non trouvé',
                'message' => "Aucun devoir trouvé avec le nom : {$shortcode}",
                'shortcode' => $shortcode
            ]);
        }

        // Check if devoir is still open
        if (!$this->devoirModel->isOpen($devoir['iddevoirs'])) {
            return $this->view('deposes/closed', [
                'title' => 'Devoir fermé',
                'message' => "Le devoir {$shortcode} est fermé. La date limite était le " . date('d/m/Y', strtotime($devoir['datelimite'])),
                'shortcode' => $shortcode,
                'devoir' => $devoir
            ]);
        }

        // Display submission form
        return $this->view('deposes/form', [
            'title' => 'Déposer votre DM - ' . $shortcode,
            'devoir' => $devoir,
            'shortcode' => $shortcode
        ]);
    }

    /**
     * Process submission form for a specific devoir
     *
     * @param Request $request
     * @param string $shortcode Devoir shortcode from URL
     * @return Response
     */
    public function deposeSubmit(Request $request, string $shortcode)
    {
        // Find devoir by shortcode
        $devoir = $this->devoirModel->findByShortcode($shortcode);

        // Check if devoir exists and is open
        if (!$devoir || !$this->devoirModel->isOpen($devoir['iddevoirs'])) {
            return $this->view('deposes/closed', [
                'title' => 'Devoir fermé ou inexistant',
                'message' => "Impossible de déposer pour ce devoir.",
                'shortcode' => $shortcode
            ]);
        }

        // Get form data
        $data = $request->all();

        // Validation rules
        $rules = [
            'prenom' => 'required|min:2|max:50',
            'nom' => 'required|min:2|max:50',
        ];

        // Create validator
        $validator = new Validator($data, $rules);

        // Validate
        if (!$validator->validate()) {
            return $this->view('deposes/form', [
                'title' => 'Déposer votre DM - ' . $shortcode,
                'devoir' => $devoir,
                'shortcode' => $shortcode,
                'errors' => $validator->errors(),
                'old' => $data
            ]);
        }

        // Prepare submission data
        $submissionData = [
            'nom' => $data['nom'],
            'prenom' => $data['prenom'],
            'iddevoirs' => $devoir['iddevoirs'],
            'url' => $data['github_url'] ?? null,
        ];

        // Handle file upload if provided
        if (isset($_FILES['fichier']) && $_FILES['fichier']['error'] !== UPLOAD_ERR_NO_FILE) {
            $file = $_FILES['fichier'];
            
            // Check for upload errors
            if ($file['error'] !== UPLOAD_ERR_OK) {
                $uploadErrors = [
                    UPLOAD_ERR_INI_SIZE => 'Le fichier dépasse la taille maximale autorisée.',
                    UPLOAD_ERR_FORM_SIZE => 'Le fichier dépasse la taille maximale du formulaire.',
                    UPLOAD_ERR_PARTIAL => 'Le fichier n\'a été que partiellement téléchargé.',
                    UPLOAD_ERR_NO_TMP_DIR => 'Dossier temporaire manquant.',
                    UPLOAD_ERR_CANT_WRITE => 'Échec de l\'écriture du fichier sur le disque.',
                    UPLOAD_ERR_EXTENSION => 'Une extension PHP a arrêté l\'upload.',
                ];
                
                return $this->view('deposes/form', [
                    'title' => 'Déposer votre DM - ' . $shortcode,
                    'devoir' => $devoir,
                    'shortcode' => $shortcode,
                    'errors' => ['fichier' => [$uploadErrors[$file['error']] ?? 'Erreur inconnue lors de l\'upload']],
                    'old' => $data
                ]);
            }
            
            // Validate file size (10MB max)
            $maxSize = 10 * 1024 * 1024; // 10 MB
            if ($file['size'] > $maxSize) {
                return $this->view('deposes/form', [
                    'title' => 'Déposer votre DM - ' . $shortcode,
                    'devoir' => $devoir,
                    'shortcode' => $shortcode,
                    'errors' => ['fichier' => ['Le fichier est trop volumineux. Taille maximale : 10 MB']],
                    'old' => $data
                ]);
            }
            
            // Get file extension
            $originalName = $file['name'];
            $extension = pathinfo($originalName, PATHINFO_EXTENSION);
            
            // Generate unique filename
            $uniqueName = uniqid() . '_' . time() . '.' . $extension;
            
            // Define upload directory (relative to document root)
            $uploadDir = __DIR__ . '/../../filestore/';
            
            // Create directory if it doesn't exist
            if (!is_dir($uploadDir)) {
                mkdir($uploadDir, 0755, true);
            }
            
            // Full path for the file
            $uploadPath = $uploadDir . $uniqueName;
            
            // Move uploaded file
            if (move_uploaded_file($file['tmp_name'], $uploadPath)) {
                // Add file information to submission data
                $submissionData['nomfichieroriginal'] = $originalName;
                $submissionData['nomfichierstockage'] = $uniqueName;
            } else {
                return $this->view('deposes/form', [
                    'title' => 'Déposer votre DM - ' . $shortcode,
                    'devoir' => $devoir,
                    'shortcode' => $shortcode,
                    'errors' => ['fichier' => ['Échec de l\'enregistrement du fichier']],
                    'old' => $data
                ]);
            }
        }

        // Save submission
        $submissionId = $this->deposeModel->createSubmission($submissionData);

        if ($submissionId) {
            return $this->view('deposes/success', [
                'title' => 'Dépôt réussi',
                'devoir' => $devoir,
                'shortcode' => $shortcode,
                'prenom' => $data['prenom'],
                'nom' => $data['nom']
            ]);
        } else {
            return $this->view('deposes/form', [
                'title' => 'Déposer votre DM - ' . $shortcode,
                'devoir' => $devoir,
                'shortcode' => $shortcode,
                'errors' => ['general' => ['Une erreur est survenue lors de l\'enregistrement']],
                'old' => $data
            ]);
        }
    }
}
