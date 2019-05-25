<script>
    $(document).ready(() => {
        function Carousel(el) {

            let TRANSITION_DELAY = 0;
            let CURRENT_ANIMATION = Promise.resolve();
            const AUTO_TRANSITION_INTERVAL = 3000;
            const ANIMATION_DURATION = 400;

            function fadeItemOutAsync(item, maybeIndicator) {
                return new Promise((resolve, reject) => {
                    item.classList.remove("slide-in");
                    item.classList.add("slide-out");
                    if (maybeIndicator) {
                        maybeIndicator.classList.remove("selected");
                    }
                    setTimeout(() => {
                        item.classList.remove("slide-out");
                        item.classList.remove("visible");
                        item.classList.remove("initial-image");
                        resolve();
                    }, ANIMATION_DURATION);
                });
            }

            function fadeItemInAsync(item, maybeIndicator) {
                return new Promise((resolve, reject) => {
                    item.classList.remove("slide-out");
                    item.classList.add("visible");
                    item.classList.add("slide-in");
                    if (maybeIndicator) {
                        maybeIndicator.classList.add("selected");
                    }
                    setTimeout(() => {
                        resolve();
                    }, ANIMATION_DURATION);
                });
            }

            function getCurrentIndex() {
                return el.querySelector(".carousel-item-container.slide-in").getAttribute("data-index");
            }

            function getNumberOfItems() {
                return el.querySelectorAll(".carousel-item-container").length;
            }

            function changeSelectedItem(index) {
                CURRENT_ANIMATION = CURRENT_ANIMATION.then(async () => {
                    if (getCurrentIndex() === index) {
                        return;
                    }
                    const currentImage = el.querySelector(".carousel-item-container.slide-in");
                    const currentIndicator = el.querySelector(".indicator.selected");
                    const targetImage = el.querySelector(`.carousel-item-container[data-index="${index}"]`);
                    const targetIndicator = el.querySelector(`.indicator[data-index="${index}"]`);
                    await Promise.all([
                        fadeItemOutAsync(currentImage, currentIndicator),
                        fadeItemInAsync(targetImage, targetIndicator)
                    ]);
                });
            }

            function maybeTransitionToNextImage() {
                TRANSITION_DELAY -= AUTO_TRANSITION_INTERVAL;
                if (TRANSITION_DELAY > 0) {
                    return;
                } else {
                    TRANSITION_DELAY = 0;
                }
                const nextIndex = (getCurrentIndex() % getNumberOfItems()) + 1;
                changeSelectedItem(nextIndex);
            }

            function onIndicatorClicked(event) {
                const index = event.target.getAttribute("data-index");
                changeSelectedItem(index);
                /* Only start transitioning again after 5s */
                TRANSITION_DELAY = 5000;
            }

            for (const indicator of el.querySelectorAll(".indicator")) {
                indicator.addEventListener("click", onIndicatorClicked);
            }

            if (el.querySelectorAll("img").length > 1) {
                setInterval(maybeTransitionToNextImage, AUTO_TRANSITION_INTERVAL);
            }
        }

        $(document).ready(() => {
            for (const carousel of document.querySelectorAll(".carousel")) {
                Carousel(carousel);
            }
        });
    })
</script>
