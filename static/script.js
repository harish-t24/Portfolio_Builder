function showSection(id) {
    document.querySelectorAll('.section')
        .forEach(s => s.style.display = 'none');
    document.getElementById(id).style.display = 'block';
}

showSection('home');
