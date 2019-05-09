<script>
    function FavoritingButton(el, characterName, onFavourited, onUnfavourited) {
        el.addEventListener("click", event => {
            $.ajax({
                url: `/favourite/${encodeURIComponent(characterName)}`,
                method: "POST"
            }).done((data, textStatus, xhr) => {
                if (xhr.status == 201) {
                    onFavourited();
                } else if (xhr.status === 204) {
                    onUnfavourited();
                }
                el.blur();
            });
        });
    }
</script>
