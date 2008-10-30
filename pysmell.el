;;; pysmell.el --- Complete python code using heuristic static analysis

;; Author: Tom Wright <tat.wright@tat.wright.name>
;; Keywords: python completion pysmell

;; This code is released under a BSD license.

;;; INSTALLATION:

;; To install:
;; * Ensure pysmell has been installed with setup.py
;; * Add this directory to your emacs load-path
;; * Require pysmell on startup
;; * Start pysmell mode whenever python mode is started by adding it to a mode hook.
;; This can be done by adding the following lines to your .emacs file
;; (add-to-list 'load-path "PATH TO DIRECTORY")
;; (require 'pysmell)
;; (add-hook 'python-mode-hook (lambda () (pysmell-mode 1)))


;;; ALTERNATIVE INSTALLATION FOR THOSE WHO HATE setuputils OR LIKE CHANGING THINGS:

;; To install this:
;; * Unzip the pysmell tarball to a directory
;; * Add this directory to your emacs load-path
;; * Require pysmell on startup
;; * Start pysmell mode whenever python mode is started by adding it to a mode hook.
;; This can be done by adding the following lines to your .emacs file
;; (add-to-list 'load-path "PATH TO DIRECTORY")
;; (require 'pysmell)
;; (add-hook 'python-mode-hook (lambda () (pysmell-mode 1)))

;; This allows one to edit the python source code.

;; [If adding something to your load-path seems cumbersome you can instead place pysmell.el in your load-path
;; and then set the variable pysmell-python-dir to point to an unzipped version of the pysmell tarball, 
;; or simply place an unzipped version of the pysmell tarball to a directory in your load-path.]

;;; MINIMAL USAGE INSTRUCTIONS:

;; * Follow the installation instructions
;; * Open a python file (ensure the Pysmell appears in the modeline)
;; * Run M-x pysmell-make-tags in some directory containing the directory tree containing the current file.
;; * Press M-/ to complete a symbols using pysmell


;;; Documentation:
;; PySmell will try to intelligently complete symbol in Python
;; based on the current context. For example, within a class A's method
;; completing after "self.f" with only cycle through those
;; methods of A and A's parent class's properties - rather 
;; than any word that happens to begin with f in any buffer.

;; PySmell works in a similar fashion to etags. First a large
;; data file is created by running a separate utility - in this
;; case pysmelltags.py, after this file has been produced PySmell
;; searches the files to find possible completions. This means
;; that if this data file gets out of date PySmell may not find
;; completions or may produce spurious completions. When 
;; a developers annoyance with this exceeds there
;; laziness they will recreate the tags file. The 
;; command pysmell-make-tags will produce this data file

;; PySmell was written by a Python programmer to handle Python code,
;; and was therefore, unsuprisingly, written mainly in Python. This has the advantage
;; of producing a cross platform utility that can run with almost
;; all editors. It has the disadvantage that 
;; the users of said editors have to jump through hoops to to bind
;; their editor to python. In particular, emacs users must have the pymacs 
;; package installed.

;;; Caveats:

;; PySmell is strictly a static analysis tool - so cannot deal
;; with forms of metaprogramming, where properties are added to
;; classes programmatically.

;; For strange (and probably bad) reasons it was expedient to make pysmell insert
;; a single character of spurious white-space when no completions are found
;; when completing after a single dot with no following characters. (Worse is better.)

; Integration of pysmell with autocompletion


(require 'pymacs)
(require 'hippie-exp)
(require 'cl)


(pymacs-terminate-services)


(setq pysmell-python-dir nil)
(defvar pysmell-python-dir nil "Type of matching to perform")
(defvar pysmell-matcher "case-sensitive" "Type of matching to perform")

;scour load-path for a directory containing pysmell
(if (null pysmell-python-dir)
    (dolist (dir load-path)
      (if (and
	   (file-directory-p dir)
	   (member "pysmell" (directory-files dir)))
	  (setq pysmell-python-dir (format "%s/%s" (directory-file-name dir) 
					   "pysmell")))))

;scour load-path for a directory which is pysmell
(if (null pysmell-python-dir)
    (dolist (dir load-path)
      (if (file-directory-p dir)
	  (let ((files (directory-files dir)))
	    (if (and
		 (member "emacshelper.py" files)
		 (member "idehelper.py" files))
		(setq pysmell-python-dir dir))))))


(if (not (null pysmell-python-dir))
    (progn
      (pymacs-load (expand-file-name (format "%s/%s" pysmell-python-dir "pysmell.emacshelper")) "pysmell-")
      (setq pysmell-make-tags-process
	    (list
	     "python"
	     (format "%s/%s/%s" (expand-file-name pysmell-python-dir) "pysmell" "pysmell.py"))))
  (progn
    (pymacs-load "pysmell.emacshelper" "pysmell-")
    (setq pysmell-make-tags-process (list "pysmell"))))



(defun pysmell-all-completions ()
    (setq completions (pysmell-get-completions 
		       (buffer-file-name)
		       (buffer-string)
		       (line-number-at-pos)
		       (current-column)
		       pysmell-matcher))
    (lambda () (pop completions)))



(defun pysmell-first-completion ()
  (interactive)
  (insert (funcall (pysmell-all-completions))))

  
(defun pysmell-make-tags (directory)
  "Makes tags in the current tree"
  (interactive "D")
  (let ((directory (expand-file-name directory)))
    (setq args
	  (append 
	   (list "make-pysmell-tags" "*make-pysmell-tags*")
	   pysmell-make-tags-process
	   (list directory "-o" (format "%s/%s" directory "PYSMELLTAGS"))))
    (apply 'start-process args)
  (switch-to-buffer-other-window "*make-pysmell-tags*")))


(setq pymsell-completion-iterator nil)


(defun try-pysmell-complete (old)
  "Cycle through pysmell completions for the text behind the point"
  (interactive "P")
  (let (sub)
    (if (not old)
	(setq pysmell-completion-iterator (pysmell-all-completions)))
    (if (null old)
	(let ((region (pysmell-find-subst-region)))
	      (if region
		  (apply 'he-init-string region)
		(he-init-string 
		 (point)
		 (progn
		   (insert " ")
		   (point)))))))

    (if (setq sub (funcall pysmell-completion-iterator))
	(he-substitute-string sub)
      (he-reset-string))
    (not (null sub)))


(fset 'pysmell-complete (make-hippie-expand-function '(try-pysmell-complete) t))
     
(defun pysmell-find-subst-region ()
  "Find the region which the pysmell completion should replace"
  (save-excursion 
    (destructuring-bind (beg . end) 
	(or (bounds-of-thing-at-point 'symbol) 
	    (cons (point) 
		  (progn (insert " ") (point))))
      (list beg end))))


(define-minor-mode pysmell-mode
  "Toggle PySmell mode.
With no argument, this command toggles the mode.
Non-null prefix argument turns on the mode.
Null prefix argument turns off the mode.

When PySmell mode is enabled, M-/ uses PySmell 
to complete the current symbol using heuristic 
static analysis."

 ;; The initial value.
 nil
 ;; The indicator for the mode line.
 " PySmell"
 ;; The minor mode bindings.
 `((,(kbd "M-/") . pysmell-complete))
 :group 'pysmell)




(provide 'pysmell)

;;; ends here
     
