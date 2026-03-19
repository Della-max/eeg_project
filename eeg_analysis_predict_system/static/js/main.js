// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查图像是否加载成功
    checkImagesLoad();
    
    // 添加页面交互效果
    addHoverEffects();
    
    // 平滑滚动
    setupSmoothScroll();
});

function checkImagesLoad() {
    const images = document.querySelectorAll('.result-image');
    
    images.forEach(img => {
        // 监听图像加载错误
        img.addEventListener('error', function() {
            // 创建错误提示
            const errorDiv = document.createElement('div');
            errorDiv.className = 'image-error';
            errorDiv.textContent = '无法加载图像: ' + img.alt;
            
            // 替换图像或在下方显示错误
            img.parentNode.insertBefore(errorDiv, img.nextSibling);
            
            // 可以选择隐藏无法加载的图像
            // img.style.display = 'none';
        });
        
        // 监听图像加载成功
        img.addEventListener('load', function() {
            console.log('图像加载成功: ' + img.alt);
        });
    });
}

function addHoverEffects() {
    const containers = document.querySelectorAll('.image-container');
    
    containers.forEach(container => {
        container.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        container.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

function setupSmoothScroll() {
    // 平滑滚动到页面内锚点
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 20,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// 添加图像刷新功能
function refreshImages() {
    const images = document.querySelectorAll('.result-image');
    
    images.forEach(img => {
        // 添加时间戳以防止缓存
        const timestamp = new Date().getTime();
        const originalSrc = img.src.split('?')[0];
        img.src = originalSrc + '?' + timestamp;
    });
}

// 暴露refreshImages函数供全局使用
window.refreshImages = refreshImages;