
function toggleSidebar() {
    let sidebar = document.querySelector('.sidebar');
    let main = document.querySelector('.main');
    let isSmallScreen = window.innerWidth <= 768;

    if (sidebar.style.right === "-250px") {
        sidebar.style.right = "0px";
        if (!isSmallScreen) main.style.marginRight = "250px";
    } else {
        sidebar.style.right = "-250px";
        if (!isSmallScreen) main.style.marginRight = "0px";
    }
}