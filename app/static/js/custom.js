$(document).ready(function() {
    $('[data-toggle="tooltip"]').tooltip();

    $('.toggle-password').on('click', function() {
        const mask = $(this).siblings('.password-mask');
        const password = mask.data('password');
        const isShowing = mask.data('showing');

        if (isShowing) {
            mask.text('••••••••');
            mask.data('showing', false);
            $(this).find('i').removeClass('ti-eye-off').addClass('ti-eye');
        } else {
            mask.text(password);
            mask.data('showing', true);
            $(this).find('i').removeClass('ti-eye').addClass('ti-eye-off');
        }
    });
});
