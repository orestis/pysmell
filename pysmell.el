;;; pysmell.el --- Complete python code using heuristic static analysis

;; Author: Tom Wright <tat.wright@tat.wright.name>
;; Keywords: python completion pysmell
;; Version: 0.7.2

;; Bug reports should be filed at <http://code.google.com/p/pysmell>

;; This code is released under a BSD license.

;;; INSTALLATION:

;; To install:
;; * Install pysmell (python setup.py install)
;; * Add pysmell.el to your emacs load-path
;; * Install pymacs.el and make sure it's working
;; * Require pysmell on startup
;; * Start pysmell mode whenever python mode is started by adding it to a mode hook.
;; This can be done by adding the following lines to your .emacs file
;; (add-to-list 'load-path "PATH TO DIRECTORY")
;; (require 'pysmell)
;; (add-hook 'python-mode-hook (lambda () (pysmell-mode 1)))

;;; DEVELOPING

;; If you want to hack on the Python part of PySmell, you can do
;; 'python setup.py develop' instead of 'install'. This will create
;; symlinks instead of copying the files in site-packages, meaning
;; that changes will be picked up automatically.

;;; MINIMAL USAGE INSTRUCTIONS:

;; * Follow the installation instructions
;; * Open a python file (ensure the Pysmell appears in the modeline)
;; * Run M-x pysmell-make-tags in some directory containing the directory tree containing the current file.
;; * Press M-/ to complete a symbol using pysmell

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
;; completions or may produce spurious completions. You can always
;; regenerate this file with pysmell-make-tags. Look into the main
;; documentation for more examples, including external libraries.

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

(defvar pysmell-matcher "case-sensitive" "Type of matching to perform")

(pymacs-load "pysmell.emacshelper" "pysmell-")
(setq pysmell-make-tags-process (list "pysmell"))


(defun pysmell-get-all-completions ()
  "Get all the completions for the symbol under the point."
  (pysmell-get-completions 
   (buffer-file-name)
   (buffer-string)
   (line-number-at-pos)
   (current-column)
   pysmell-matcher))


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


(setq pysmell-completions nil)
(defun try-pysmell-complete (old)
  "Cycle through pysmell completions for the text behind the point"
  (interactive "P")
  (let (sub)
    (if (not old)
	(setq pysmell-completions (pysmell-get-all-completions)))
    (if (null old)
	(let ((region (pysmell-find-subst-region)))
	      (if region
		  (apply 'he-init-string region)
		(he-init-string 
		 (point)
		 (progn
		   (insert " ")
		   (point)))))))
    (if (setq sub (pop pysmell-completions))
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

;;; pysmell.el ends here
     
