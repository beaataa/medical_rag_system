document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('question-form');
    const questionInput = document.getElementById('question');
    const loadingDiv = document.getElementById('loading');
    const responseDiv = document.getElementById('response');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Show loading indicator
        loadingDiv.style.display = 'block';
        responseDiv.textContent = '';
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question }),
            });
            
            const data = await response.json();
            
            if (data.error) {
                responseDiv.textContent = `Error: ${data.error}`;
            } else {
                responseDiv.textContent = data.response;
            }
        } catch (error) {
            responseDiv.textContent = `An error occurred: ${error.message}`;
        } finally {
            // Hide loading indicator
            loadingDiv.style.display = 'none';
        }
    });
});