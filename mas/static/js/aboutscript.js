document.addEventListener('DOMContentLoaded', () => {
    const handleScroll = () => {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach((el) => {
            const rect = el.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight - 100;
            if (isVisible) {
                el.classList.add('translate-y-0', 'opacity-100');
                el.classList.remove('translate-y-20', 'opacity-0');
            } else {
                el.classList.remove('translate-y-0', 'opacity-100');
                el.classList.add('translate-y-20', 'opacity-0');
            }
        });
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll();
});