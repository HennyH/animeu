<script>
     $(document).ready(() => {
        const VIEWS = [
            "picture-view",
            "info-view",
            "description-view"
        ];

        function resetCardView({ $card, deactivateButtons = false, keepViews = [] }) {
            for (const view of VIEWS) {
                if (keepViews.some(v => view === v)) {
                    continue;
                }
                $card.removeClass(view);
                if (deactivateButtons) {
                    $card.find(`.toggle-${view}`).removeClass("active");
                }
            }
        }

        function toggleCardView(viewToToggle, $allCards, $selectedCards, singleExpand) {
            $allCards.removeClass("hidden");

            const selectedCards = $selectedCards.toArray();
            for (const card of $allCards) {
                const $card = $(card)
                if (selectedCards.some(sc => sc.id === $card.prop("id"))) {
                    if ($card.hasClass(viewToToggle)) {
                        resetCardView({ $card, deactivateButtons: true });
                        $card.addClass("info-view");
                    } else {
                        resetCardView({ $card,deactivateButtons: true,  keepViews: [viewToToggle] });
                        $card.addClass(viewToToggle);
                        $card.find(`.toggle-${viewToToggle}`).addClass("active");
                    }
                }
            }
        }

        $(".toggle-picture-view").click(e => {
            const $allCards = $(".character-card");
            const clickedButton = $(e.target);
            const $selectedCards = e.ctrlKey
                ? $allCards
                : clickedButton.closest(".character-card");
            toggleCardView("picture-view", $allCards, $selectedCards);
            e.preventDefault();
            e.stopPropagation();
        });

        $(".toggle-description-view").click(e => {
            const $allCards = $(".character-card");
            const clickedButton = $(e.target);
            const $selectedCards = e.ctrlKey
                ? $allCards
                : clickedButton.closest(".character-card");
            toggleCardView("description-view", $allCards, $selectedCards);
            e.preventDefault();
            e.stopPropagation();
        });

        $(".jump-to-top").click(e => {
            const yOffset = Math.max(0, $(e.target).closest(".character-card").offset().top - 20);
            window.scroll({ top: yOffset });
            e.preventDefault();
            e.stopPropagation();
        });
    });
</script>
