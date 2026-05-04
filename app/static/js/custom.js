document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-password').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const mask = this.parentElement.querySelector('.password-mask');
            const password = mask.dataset.password;
            const isShowing = mask.dataset.showing === 'true';

            if (isShowing) {
                mask.textContent = '••••••••';
                mask.dataset.showing = 'false';
                this.querySelector('i').classList.remove('ti-eye-off');
                this.querySelector('i').classList.add('ti-eye');
            } else {
                mask.textContent = password || 'N/A';
                mask.dataset.showing = 'true';
                this.querySelector('i').classList.remove('ti-eye');
                this.querySelector('i').classList.add('ti-eye-off');
            }
        });
    });
});
