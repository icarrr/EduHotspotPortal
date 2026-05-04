document.addEventListener('DOMContentLoaded', function() {
    // Password toggle
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

    // Bulk delete checkboxes
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.user-checkbox');
    const deleteBtn = document.getElementById('bulk-delete-btn');
    const countSpan = document.getElementById('selected-count');
    const bulkForm = document.getElementById('bulk-delete-form');

    if (selectAll && checkboxes.length > 0) {
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(cb => cb.checked = this.checked);
            updateSelectedCount();
        });

        checkboxes.forEach(cb => {
            cb.addEventListener('change', updateSelectedCount);
        });
    }

    function updateSelectedCount() {
        const count = document.querySelectorAll('.user-checkbox:checked').length;
        if (countSpan) countSpan.textContent = count;
        if (deleteBtn) deleteBtn.disabled = count === 0;

        // Update hidden inputs in form
        document.querySelectorAll('#bulk-delete-form input[name="usernames"]').forEach(i => i.remove());
        document.querySelectorAll('.user-checkbox:checked').forEach(cb => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'usernames';
            input.value = cb.value;
            bulkForm.appendChild(input);
        });
    }
});
