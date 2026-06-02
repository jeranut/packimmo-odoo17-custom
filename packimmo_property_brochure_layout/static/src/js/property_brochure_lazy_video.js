document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".pk-video-wrapper").forEach(function(wrapper) {

        wrapper.addEventListener("click", function () {

            const url = wrapper.dataset.video;

            let videoId = '';

            try {

                const parsed = new URL(url);

                if (parsed.hostname.includes('youtu.be')) {

                    videoId = parsed.pathname.replace('/', '');

                } else {

                    videoId = parsed.searchParams.get('v');

                }

            } catch(e) {
                console.error(e);
            }

            if (!videoId) {
                return;
            }

            wrapper.innerHTML = `
                <iframe
                    width="100%"
                    height="420"
                    src="https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0"
                    title="YouTube video player"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowfullscreen>
                </iframe>
            `;

        });

    });

});