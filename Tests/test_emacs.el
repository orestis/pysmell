;; Press key
(defun press-key (key)
  (call-interactively (key-binding key t)))

(defun assert-word-at-point (expected &optional msg)
  (interactive)
  (let ((actual (thing-at-point 'word))
	(msg (or msg "")))
    (unless (equal actual expected)
      (error "word at point wrong. '%s' != '%s': %s" actual expected msg))))

(defun run-test (test)
  (condition-case err
      (funcall test)
    (error 
     (progn
       (print err)
       (kill-emacs 1)))))

(defun string-in-bufferp (string)
  "Check if a string is in the current buffer"
  (goto-char 0)
  (search-forward "finished" nil t))


(defun test-basic ()
  ;; Harold wants pysmell completion to more or less work
  
  ;; He adds a directory containing pysmell.el to his load-path
  (add-to-list 'load-path ".")

  ;; He loads pysmell
  (require 'pysmell)

  ;; He opens a new file in the TestData folder and switches on pysmell mode.
  (setq input-buffer (find-file "TestData/test.py"))


  ;; He runs pysmell-make-tags on the TestData directory
  (pysmell-make-tags ".")

  ;; A new buffer is displayed with the name "*make-pysmell-tags*"
  (assert (equal (buffer-name) "*make-pysmell-tags*"))

  ;; He does nothing for a while
  (sit-for 3) ;;; yay for non-determinism - someone more intelligent can fix this. - beware blocking sleeps.
  (assert (not (string-in-bufferp "EXCEPTION")))

  ;; He switches back to his new file.
  (switch-to-buffer input-buffer)
  (pysmell-mode 1)

  ;; He wants some form of completion to work
  ;; He enters the following text "from PackageA.ModuleA import ClassA\no = ClassA()\no."
  (insert "from PackageA.ModuleA import ClassA\no = ClassA()\no.")

  ;; He presses "M-/"
  (press-key (kbd "M-/"))

  ;; The word under the point is "classPropertyA"
  (print (buffer-string))
  (assert-word-at-point "classPropertyA")

  ;; He presses "M-/" again

  (press-key (kbd "M-/"))

  ;; The word under the point is "classPropertyB" 
  (assert-word-at-point "classPropertyB"))

(defun run-all-tests ()
  (run-test 'test-basic))
