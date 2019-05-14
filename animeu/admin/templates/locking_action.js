<script>
    function LockingAction({
            el,
            actionUrl,
            startOptsFactory = () => {},
            pollOptsFactory = () => {},
            deleteOptsFactory = () => {},
            pollingInterval = 5000
    }) {
        const performActionBtn = el.querySelector("button.perform-action");
        const deleteLockBtn = el.querySelector("button.delete-lock");
        const progressBar = el.querySelector(".progress-bar");
        const status = el.querySelector(".action-status");
        let IS_POLLING = false;

        function pollActionProgress() {
            if (IS_POLLING) {
                return;
            }
            const interval = setInterval(() => {
                IS_POLLING = true;
                progressBar.classList.add("progress-bar-animated");
                progressBar.classList.add("progress-bar-striped");
                $.ajax({
                    url: actionUrl,
                    method: "GET",
                    ...(pollOptsFactory() || {})
                }).then((data, textStatus, xhr) => {
                    if (xhr.status === 200) {
                        progressBar.style = `width: ${escape(data)}%`
                        if (data >= 98) {
                            clearInterval(interval);
                            progressBar.style = `width: 100%`;
                            performActionBtn.textContent = "Complete";
                            status.textContent = "Completed just now.";
                            progressBar.classList.remove("progress-bar-animated");
                            progressBar.classList.remove("progress-bar-striped ");
                            IS_POLLING = false;
                        }
                    }
                });
            }, pollingInterval);
        }

        function tryStartAction() {
                $.ajax({
                    url: actionUrl,
                    method: "POST",
                    ...(startOptsFactory() || {})
                }).then((data, textStatus, xhr) => {
                    /* if unavaliable disable the button */
                    if (xhr.status === 503) {
                        performActionBtn.classList.replace("btn-primary", "btn-danger");
                        performActionBtn.disabled = true;
                        performActionBtn.textContent = "Service Unavailable Try Again Later";
                    } else if (xhr.status === 200 || xhr.status === 201) {
                        performActionBtn.classList.replace("btn-primary", "btn-success");
                        performActionBtn.disabled = true;
                        performActionBtn.textContent = "Performing Action...";
                        pollActionProgress();
                    }
                })
            }

        function tryDeleteLock() {
            $.ajax({
                url: actionUrl,
                method: "DELETE",
                ...(deleteOptsFactory() || {})
            }).then((data, textStatus, xhr) => {
                if (xhr.status === 200) {
                    deleteLockBtn.textContent = "Lock Removed";
                    deleteLockBtn.disabled = true;
                } else if (xhr.status === 304) {
                    deleteLockBtn.textContent = "No Lock Exists";
                    deleteLockBtn.disabled = true;
                } else {
                    deleteLockBtn.textContent = "Could Not Delete Lock";
                    deleteLockBtn.disabled = true;
                }
            })
        }

        performActionBtn.addEventListener("click",  tryStartAction);
        deleteLockBtn.addEventListener("click", tryDeleteLock);
        console.log(progressBar.getAttribute("data-start-polling") === "true")
        if (progressBar.getAttribute("data-start-polling") === "true") {
            pollActionProgress()
        }
    }
</script>