document.addEventListener('DOMContentLoaded', function() {
    // Progress ring animation
    const progressRings = document.querySelectorAll('.circular-progress');
    progressRings.forEach(ring => {
        const percentage = ring.dataset.percentage;
        const circle = ring.querySelector('.progress-ring-circle');
        const circumference = 2 * Math.PI * 30;
        const offset = circumference - (percentage / 100) * circumference;
        
        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = offset;
    });
    
    // Quick enrollment
    document.querySelectorAll('.quick-enroll-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            
            fetch('{% url "enrollment:quick_enroll" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: `course_id=${courseId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('خطایی رخ داد. لطفاً دوباره تلاش کنید.', 'error');
            });
        });
    });
    
    // Enrollment cancellation
    let enrollmentToCancel = null;
    
    document.querySelectorAll('.cancel-enrollment').forEach(btn => {
        btn.addEventListener('click', function() {
            enrollmentToCancel = this.dataset.enrollmentId;
            const modal = new bootstrap.Modal(document.getElementById('cancelEnrollmentModal'));
            modal.show();
        });
    });
    
    document.getElementById('confirmCancellation').addEventListener('click', function() {
        if (!enrollmentToCancel) return;
        
        const reason = document.getElementById('cancellationReason').value;
        
        fetch(`{% url 'enrollment:cancel_enrollment' 0 %}`.replace('0', enrollmentToCancel), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({reason: reason})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.message, 'error');
            }
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('cancelEnrollmentModal'));
            modal.hide();
        })
        .catch(error => {
            showNotification('خطایی رخ داد. لطفاً دوباره تلاش کنید.', 'error');
        });
    });
});

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
} 