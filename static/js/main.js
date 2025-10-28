(function () {
    const settingsLink = document.getElementById('settingsLink');
    const applyThemeButton = document.getElementById('applyTheme');
    const zoomInButton = document.getElementById('zoomIn');
    const zoomOutButton = document.getElementById('zoomOut');

    if (settingsLink) {
        settingsLink.addEventListener('click', function () {
            $('#settingsModal').modal('show');
        });
    }

    if (applyThemeButton) {
        applyThemeButton.addEventListener('click', function () {
            const selectedTheme = document.querySelector('input[name="theme"]:checked').value;
            if (selectedTheme === 'black') {
                document.body.style.backgroundColor = 'black';
                document.body.style.color = 'white';
            } else if (selectedTheme === 'green') {
                document.body.style.backgroundColor = 'green';
                document.body.style.color = 'white';
            } else {
                document.body.style.backgroundColor = '#f8f9fa';
                document.body.style.color = 'black';
            }
            $('#settingsModal').modal('hide');
        });
    }

    if (zoomInButton) {
        zoomInButton.addEventListener('click', function () {
            document.body.style.zoom = '115%';
        });
    }

    if (zoomOutButton) {
        zoomOutButton.addEventListener('click', function () {
            document.body.style.zoom = '100%';
        });
    }
})();
