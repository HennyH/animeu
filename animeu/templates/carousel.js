<script>
    $(document).ready(() => {
        function Carousel(el) {

            let TRANSITION_DELAY = 0;
            let CURRENT_ANIMATION = Promise.resolve();
            const AUTO_TRANSITION_INTERVAL = 3000;

            function fadeImageOutAsync(img) {
                return new Promise((resolve, reject) => {
                    img.classList.remove("fade-in");
                    img.classList.add("fade-out");
                    setTimeout(() => {
                        img.classList.remove("fade-out");
                        img.classList.remove("visible");
                        resolve();
                    }, 600);
                });
            }

            function fadeImageInAsync(img) {
                return new Promise((resolve, reject) => {
                    img.classList.remove("fade-out");
                    img.classList.add("visible");
                    img.classList.add("fade-in");
                    setTimeout(() => {
                        resolve();
                    }, 600);
                });
            }

            function getCurrentIndex() {
                return el.querySelector("img.fade-in").getAttribute("data-index");
            }

            function getNumberOfImages() {
                return el.querySelectorAll("img").length;
            }

            function changeToImage(index) {
                CURRENT_ANIMATION = CURRENT_ANIMATION.then(async () => {
                    const currentImage = el.querySelector("img.fade-in");
                    const currentIndicator = el.querySelector(".indicator.active");
                    const targetImage = el.querySelector(`img[data-index="${index}"]`);
                    const targetIndicator = el.querySelector(`.indicator[data-index="${index}"]`);
                    await Promise.all([
                        fadeImageOutAsync(currentImage),
                        fadeImageInAsync(targetImage)
                    ]);
                    if (targetIndicator && currentIndicator) {
                        currentIndicator.classList.remove("active");
                        targetIndicator.classList.add("active");
                    }
                });
            }

            function maybeTransitionToNextImage() {
                TRANSITION_DELAY -= AUTO_TRANSITION_INTERVAL;
                if (TRANSITION_DELAY > 0) {
                    return;
                } else {
                    TRANSITION_DELAY = 0;
                }
                const nextIndex = (getCurrentIndex() % getNumberOfImages()) + 1;
                changeToImage(nextIndex);
            }

            function onIndicatorClicked(event) {
                const index = event.target.getAttribute("data-index");
                changeToImage(index);
                /* Only start transitioning again after 5s */
                TRANSITION_DELAY = 5000;
            }

            for (const indicator of el.querySelectorAll(".indicator")) {
                indicator.addEventListener("click", onIndicatorClicked);
            }

            setInterval(maybeTransitionToNextImage, AUTO_TRANSITION_INTERVAL);
        }

        $(document).ready(() => {
            for (const carousel of document.querySelectorAll(".carousel")) {
                Carousel(carousel);
            }
        });
    })
</script>