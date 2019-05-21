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

            function toggleFullscreen(imgClickedEvent) {
                requestAnimationFrame(() => {
                    /* insert an overlay to capture any dismissing clicks */
                    const overlay = document.createElement("div");
                    overlay.style = "position: absolute; left: 0; top: 0; width: 100vw; height: 100vh; z-index: 999";
                    document.body.append(overlay);

                    /* we're going to use another image to do the 'scale up' transition because
                    * if we keep this one here (but not visible) we won't cause the other images
                    * in the gallery to jump around.
                    */
                    const img =  imgClickedEvent.target;
                    const imgSrc = img.getAttribute("src");
                    const imgRect = img.getBoundingClientRect();

                    const animationName = `gallery-expand`;
                    const scaleFactor = 2;
                    const animationCss = `
                        @keyframes ${animationName} {
                            0% {
                                transform:
                                    translate(calc(${imgRect.left}px - 0 * ${imgRect.width}px),
                                              calc(${imgRect.top}px - 0 * ${imgRect.height}px))
                                    scale(1);
                            }
                            100% {
                                transform:
                                    translate(calc(50vw - 0.5 * ${imgRect.width}px),
                                              calc(50vh - 0.5 * ${imgRect.height}px))
                                    scale(${scaleFactor});
                            }
                        }
                    `;
                    const undoAnimationName = `gallery-collapse`;
                    const undoAnimationCss = `
                        @keyframes ${undoAnimationName} {
                            0% {
                                transform:
                                    scale(${scaleFactor});
                                    translate(calc(50vw - 0.5 * ${imgRect.width}px),
                                              calc(50vh - 0.5 * ${imgRect.height}px))

                            }
                            100% {
                                transform:
                                    scale(1);
                                    translate(calc(${imgRect.left}px - 0.5 * ${imgRect.width}px),
                                            calc(${imgRect.top}px - 0.5 * ${imgRect.height}px))

                            }
                        }
                    `

                    const style = document.createElement("style");
                    style.innerHTML = animationCss + undoAnimationCss;
                    document.head.append(style);

                    const imgCopy = document.createElement("img");
                    imgCopy.src = imgSrc;
                    imgCopy.style = `
                        position: absolute;
                        animation: 10s ${animationName};
                        animation-fill-mode: forwards;
                    `;
                    overlay.appendChild(imgCopy);

                    function untoggleFullscreen() {
                        overlay.removeEventListener("click", untoggleFullscreen);
                        imgCopy.style = `
                            position: absolute;
                            animation: 10s ${undoAnimationName};
                            animation-fill-mode: forwards;
                        `;
                        setTimeout(() => {
                            img.style = "";
                            // style.remove();
                            overlay.remove();
                        }, 10000)
                    }

                    overlay.addEventListener("click", untoggleFullscreen);
                })

            }

            for (const indicator of el.querySelectorAll(".indicator")) {
                indicator.addEventListener("click", onIndicatorClicked);
            }

            for (const img of document.querySelectorAll("img")) {
                img.addEventListener("click", toggleFullscreen)
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
