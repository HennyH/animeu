<script>
    $(document).ready(() => {
        function Carousel(el) {

            let TRANSITION_DELAY = 0;
            let CURRENT_ANIMATION = Promise.resolve();
            const AUTO_TRANSITION_INTERVAL = 3000;

            function fadeImageOutAsync(img) {
                return new Promise((resolve, reject) => {
                    img.classList.add("fade-out");
                    setTimeout(() => {
                        img.classList.remove("fade-out");
                        resolve();
                    }, 600);
                });
            }

            function fadeImageInAsync(img) {
                return new Promise((resolve, reject) => {
                    img.classList.add("fade-in");
                    setTimeout(() => {
                        img.classList.remove("fade-in");
                        resolve();
                    }, 600);
                });
            }

            function getCurrentIndex() {
                return el.querySelector("img.active").getAttribute("data-index");
            }

            function getNumberOfImages() {
                return el.querySelectorAll("img").length;
            }

            function changeToImage(index) {
                CURRENT_ANIMATION = CURRENT_ANIMATION.then(async () => {
                    const currentImage = el.querySelector("img.active");
                    const currentIndicator = el.querySelector(".indicator.active");
                    await fadeImageOutAsync(currentImage);
                    currentImage.classList.remove("active");
                    if (currentIndicator) {
                        currentIndicator.classList.remove("active");
                    }
                    const targetImage = el.querySelector(`img[data-index="${index}"]`);
                    const targetIndicator = el.querySelector(`.indicator[data-index="${index}"]`);
                    targetImage.classList.add("active");
                    if (targetIndicator) {
                        targetIndicator.classList.add("active");
                    }
                    await fadeImageInAsync(targetImage);
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