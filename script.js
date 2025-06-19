// Global variables for pagination
let allPhotosData = [];
let currentPage = 1;
const itemsPerPage = 16; // 每页显示16张图片
let paginatedPhotos = []; // 用于分页的照片数据

// Key management variables
let validKeys = [];
let contactUnlocked = false; // 是否已解锁联系方式

// NEW: Define loadPhotos function - moved fetch('data.json') logic here
function loadPhotos() {
    const galleryContainer = document.getElementById('gallery'); // Get gallery here for safety

    // Display loading text while fetching data, only if galleryContainer is available
    if (galleryContainer) {
        galleryContainer.innerHTML = '<p id="loading-text">正在加载照片...</p>';
    }

    fetch('data.json')
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('data.json not found. Please ensure the file exists and is accessible.');
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }
            return response.json();
        })
        .then(data => {
            allPhotosData = data; // Save original data
            paginatedPhotos = data; // Initialize paginated data
            currentPage = 1; // Reset current page when new data is loaded
            setupPagination(paginatedPhotos); // Set up pagination
            displayPhotos(paginatedPhotos); // Initially display first page of photos
        })
        .catch(error => {
            console.error('Error fetching or parsing data:', error);
            const gallery = document.getElementById('gallery'); // Get gallery again in catch block for safety
            if (gallery) {
                gallery.innerHTML = `<p>加载照片失败: ${error.message || error}. 请检查 data.json 文件或控制台获取更多信息。</p>`;
            } else {
                console.error("Gallery container not found, cannot display photo loading error.");
            }
        });
}

document.addEventListener('DOMContentLoaded', () => {
    // REMOVED: const galleryContainer = document.getElementById('gallery');
    // REMOVED: const searchInput = document.getElementById('searchInput');
    const warningModal = document.getElementById('warningModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const imageModal = document.getElementById('imageModal');
    const fullImage = document.getElementById('fullImage');
    const imageCaption = document.getElementById('caption');
    const imageModalCloseBtn = imageModal ? imageModal.querySelector('.close-button') : null;

    loadKeysConfig();
    // 新增：页面加载时直接加载照片
    loadPhotos();

    // REMOVED: fetch('data.json') block (now in loadPhotos function)
    // REMOVED: searchInput.addEventListener('input', filterGallery);

    // Warning modal display and close logic (always visible initially)
    if (warningModal && closeModalBtn) {
        warningModal.style.display = 'flex';
        closeModalBtn.addEventListener('click', () => {
            warningModal.style.display = 'none';
        });
        window.addEventListener('click', (event) => {
            if (event.target === warningModal) {
                warningModal.style.display = 'none';
            }
        });
    }

    // Image modal close logic (always part of the DOM)
    if (imageModal && imageModalCloseBtn) {
        imageModalCloseBtn.addEventListener('click', () => {
            imageModal.style.display = 'none';
        });
        window.addEventListener('click', (event) => {
            if (event.target === imageModal) {
                imageModal.style.display = 'none';
            }
        });
    }

    // Key entry modal event listener (always visible initially)
    // document.getElementById('submitKeyButton').addEventListener('click', validateKey);

    // Initial warning modal display
    showWarningModal("本站为信息付费，并不对寻欢经历负责，请注意个人防范。\n\n凡是有要求路费/上门/定金/保证金/照片验证/视频验证/提前付费等类似行为的都是骗子，同时也请注意任何形式的推荐办卡行为，请勿上当受骗。\n\n碰到有问题的信息，请及时举报给我们删除信息。如果发布的信息涉及个人隐私，也请及时举报，我们会核实后第一时间帮你删除处理。");

    // 新增：右上角按钮弹出密钥弹窗
    // document.getElementById('unlockContactBtn').addEventListener('click', function() {
    //     document.getElementById('contact-key-modal').style.display = 'flex';
    // });
    document.getElementById('submitContactKeyButton').addEventListener('click', validateContactKey);

    // 搜索和重置按钮事件绑定，页面加载即生效
    const addressSearch = document.getElementById('addressSearch');
    const searchButton = document.getElementById('searchButton');
    const resetSearchButton = document.getElementById('resetSearchButton');
    if (addressSearch) {
        addressSearch.addEventListener('input', filterGallery);
    }
    if (searchButton) {
        searchButton.addEventListener('click', filterGallery);
    }
    if (resetSearchButton) {
        resetSearchButton.addEventListener('click', resetSearch);
    }
});

// Function: Display photos in the gallery
function displayPhotos(photos) {
    const galleryContainer = document.getElementById('gallery');
    if (!galleryContainer) return;
    galleryContainer.innerHTML = '';

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const photosToDisplay = photos.slice(startIndex, endIndex);

    if (photosToDisplay.length === 0) {
        galleryContainer.innerHTML = '<p>没有找到匹配的照片。</p>';
        return;
    }

    photosToDisplay.forEach(item => {
        const photoCard = document.createElement('div');
        photoCard.classList.add('photo-card');

        const img = document.createElement('img');
        img.src = item.photo_path;
        img.alt = item.full_address || '照片';
        img.onerror = () => {
            img.src = './images/placeholder.jpg';
            img.alt = '图片加载失败';
        };

        img.addEventListener('click', () => {
            if (imageModal && fullImage && imageCaption) {
                fullImage.src = item.photo_path;
                fullImage.style.display = 'block';
                fullImage.style.maxWidth = '90vw';
                fullImage.style.maxHeight = '90vh';
                imageCaption.textContent = item.full_address || '无地址信息';
                imageModal.style.display = 'flex';
            }
        });

        const cardContent = document.createElement('div');
        cardContent.classList.add('card-content');

        // 地址
        const title = document.createElement('h3');
        title.textContent = item.full_address ? `地址: ${item.full_address}` : '无地址信息';
        cardContent.appendChild(title);

        // 服务
        if (item.service) {
            const service = document.createElement('p');
            service.innerHTML = `<strong>服务:</strong> ${item.service}`;
            cardContent.appendChild(service);
        }
        // 年龄
        if (item.age) {
            const age = document.createElement('p');
            age.innerHTML = `<strong>年龄:</strong> ${item.age}`;
            cardContent.appendChild(age);
        }
        // 价格
        const price = document.createElement('p');
        price.innerHTML = `<strong>价格:</strong> ${item.price ? item.price : '自己谈'}`;
        cardContent.appendChild(price);

        // 联系方式等敏感信息
        if (contactUnlocked) {
            if (item.wechat) {
                const wechat = document.createElement('p');
                wechat.innerHTML = `<strong>微信:</strong> ${item.wechat}`;
                cardContent.appendChild(wechat);
            }
            if (item.qq) {
                const qq = document.createElement('p');
                qq.innerHTML = `<strong>QQ:</strong> ${item.qq}`;
                cardContent.appendChild(qq);
            }
            if (item.yuni) {
                const yuni = document.createElement('p');
                yuni.innerHTML = `<strong>与你:</strong> ${item.yuni}`;
                cardContent.appendChild(yuni);
            }
        } else {
            // 未解锁时显示按钮
            const unlockBtn = document.createElement('button');
            unlockBtn.textContent = '获取联系方式';
            unlockBtn.className = 'unlock-contact-btn';
            unlockBtn.addEventListener('click', function() {
                document.getElementById('contact-key-modal').style.display = 'flex';
            });
            cardContent.appendChild(unlockBtn);

            // 新增：客服提示
            const serviceTip = document.createElement('div');
            serviceTip.className = 'contact-service-tip';
            serviceTip.style.color = '#e74c3c';
            serviceTip.style.fontSize = '0.95em';
            serviceTip.style.marginTop = '8px';
            serviceTip.textContent = '联系在线客服获取密钥，与你号：23879563zhenzhen';
            cardContent.appendChild(serviceTip);
        }

        photoCard.appendChild(img);
        cardContent.style.minHeight = '120px'; // 保证卡片高度一致
        photoCard.appendChild(cardContent);
        galleryContainer.appendChild(photoCard);
    });
}

// Function: Filter gallery based on search term
function filterGallery() {
    const searchInput = document.getElementById('addressSearch'); // Get searchInput dynamically
    if (!searchInput) return; // Safety check
    const searchTerm = searchInput.value.toLowerCase().trim();
    let filteredPhotos = [];

    if (searchTerm === '') {
        filteredPhotos = allPhotosData; // 如果搜索词为空，显示所有照片
    } else {
        filteredPhotos = allPhotosData.filter(item => {
            return item.full_address && typeof item.full_address === 'string' && item.full_address.toLowerCase().includes(searchTerm);
        });
    }
    paginatedPhotos = filteredPhotos; // 更新分页数据源
    currentPage = 1; // 重置到第一页
    setupPagination(paginatedPhotos); // 重新设置分页按钮
    displayPhotos(paginatedPhotos); // 显示第一页筛选结果
}

// Function: Reset search and display all photos
function resetSearch() {
    const searchInput = document.getElementById('addressSearch'); // Get searchInput dynamically
    if (searchInput) {
        searchInput.value = '';
    }
    paginatedPhotos = allPhotosData;
    currentPage = 1;
    setupPagination(paginatedPhotos);
    displayPhotos(paginatedPhotos);
}

// Function: Set up pagination
function setupPagination(photos) {
    const paginationContainer = document.getElementById('pagination');
    if (!paginationContainer) return; // Ensure pagination container exists
    paginationContainer.innerHTML = ''; // Clear existing buttons

    const totalPages = Math.ceil(photos.length / itemsPerPage);
    if (totalPages <= 1) return;

    // 上一页按钮
    const prevButton = document.createElement('button');
    prevButton.textContent = '上一页';
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            displayPhotos(paginatedPhotos);
            updatePaginationButtons();
        }
    });
    paginationContainer.appendChild(prevButton);

    // 页码按钮（只显示部分页码和省略号）
    let pageButtons = [];
    if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) {
            pageButtons.push(i);
        }
    } else {
        pageButtons = [1];
        if (currentPage > 4) pageButtons.push('...');
        for (let i = Math.max(2, currentPage - 2); i <= Math.min(totalPages - 1, currentPage + 2); i++) {
            pageButtons.push(i);
        }
        if (currentPage < totalPages - 3) pageButtons.push('...');
        pageButtons.push(totalPages);
    }
    pageButtons.forEach(p => {
        if (p === '...') {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'pagination-ellipsis';
            paginationContainer.appendChild(ellipsis);
        } else {
            const pageButton = document.createElement('button');
            pageButton.textContent = p;
            if (p === currentPage) {
                pageButton.classList.add('active');
                pageButton.disabled = true;
            }
            pageButton.addEventListener('click', () => {
                currentPage = p;
                displayPhotos(paginatedPhotos);
                updatePaginationButtons();
            });
            paginationContainer.appendChild(pageButton);
        }
    });

    // 下一页按钮
    const nextButton = document.createElement('button');
    nextButton.textContent = '下一页';
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            displayPhotos(paginatedPhotos);
            updatePaginationButtons();
        }
    });
    paginationContainer.appendChild(nextButton);

    updatePaginationButtons();
}

// Function: Update pagination button states
function updatePaginationButtons() {
    const paginationContainer = document.getElementById('pagination');
    if (!paginationContainer) return;
    const buttons = paginationContainer.querySelectorAll('button');
    const totalPages = Math.ceil(paginatedPhotos.length / itemsPerPage);

    buttons.forEach(button => {
        button.classList.remove('active');
        button.disabled = false; // Enable all buttons by default

        if (button.textContent === String(currentPage)) {
            button.classList.add('active');
            button.disabled = true; // Disable current page button
        }
        if (button.textContent === '上一页' && currentPage === 1) {
            button.disabled = true;
        }
        if (button.textContent === '下一页' && currentPage === totalPages) {
            button.disabled = true;
        }
    });
}

async function loadKeysConfig() {
    try {
        const response = await fetch('keys_config.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        validKeys = await response.json();
        console.log('Keys config loaded:', validKeys);
    } catch (error) {
        console.error('Error loading keys config:', error);
        document.getElementById('keyMessage').textContent = '无法加载密钥配置，请联系管理员。';
        // Optionally, prevent access if keys cannot be loaded
    }
}

async function validateKey() {
    const keyInput = document.getElementById('keyInput').value.trim();
    const keyMessage = document.getElementById('keyMessage');
    keyMessage.textContent = ''; // Clear previous messages

    if (!keyInput) {
        keyMessage.textContent = '请输入密钥。';
        return;
    }

    // Hash the input key for comparison
    const encoder = new TextEncoder();
    const data = encoder.encode(keyInput);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
    const hashedKey = hashArray.map(b => b.toString(16).padStart(2, '0')).join(''); // convert bytes to hex string

    console.log('Input key:', keyInput);
    console.log('Hashed input key:', hashedKey);

    const now = Date.now() / 1000; // current time in seconds (Unix timestamp)

    let isValid = false;
    for (const key of validKeys) {
        if (key.hash === hashedKey) {
            if (key.exp === null) { // Permanent key
                isValid = true;
                break;
            } else if (key.exp > now) { // Timed key and not expired
                isValid = true;
                break;
            }
        }
    }

    if (isValid) {
        document.getElementById('key-entry-modal').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        initializeMainContent(); // Initialize main content after successful validation
    } else {
        keyMessage.textContent = '密钥无效或已过期，请重试或联系管理员。';
    }
}

function closeImageModal() {
    document.getElementById('imageModal').style.display = 'none';
}

function showWarningModal(message) {
    document.getElementById('warningMessage').textContent = message;
    document.getElementById('warningModal').style.display = 'flex'; // Use flex to center
}

function closeWarningModal() {
    document.getElementById('warningModal').style.display = 'none';
}

// Initialize Main Content - called after key validation
function initializeMainContent() {
    loadPhotos(); // Now correctly calls the defined loadPhotos function

    // Existing event listeners (ensure elements are available here)
    const addressSearch = document.getElementById('addressSearch');
    const searchButton = document.getElementById('searchButton');
    const resetSearchButton = document.getElementById('resetSearchButton');

    if (addressSearch) {
        addressSearch.addEventListener('input', filterGallery);
    }
    if (searchButton) {
        searchButton.addEventListener('click', filterGallery);
    }
    if (resetSearchButton) {
        resetSearchButton.addEventListener('click', resetSearch); // Corrected function call
    }
}

// 新增：密钥校验函数
async function validateContactKey() {
    const keyInput = document.getElementById('contactKeyInput').value.trim();
    const keyMessage = document.getElementById('contactKeyMessage');
    keyMessage.textContent = '';

    if (!keyInput) {
        keyMessage.textContent = '请输入密钥。';
        return;
    }

    // Hash the input key for comparison
    const encoder = new TextEncoder();
    const data = encoder.encode(keyInput);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
    const hashedKey = hashArray.map(b => b.toString(16).padStart(2, '0')).join(''); // convert bytes to hex string

    // 加载密钥配置
    if (!validKeys || validKeys.length === 0) {
        await loadKeysConfig();
    }
    const now = Date.now() / 1000; // current time in seconds (Unix timestamp)
    let isValid = false;
    for (const key of validKeys) {
        if (key.hash === hashedKey) {
            if (key.exp === null) { // Permanent key
                isValid = true;
                break;
            } else if (key.exp > now) { // Timed key and not expired
                isValid = true;
                break;
            }
        }
    }
    if (isValid) {
        contactUnlocked = true;
        document.getElementById('contact-key-modal').style.display = 'none';
        // 重新渲染联系方式
        displayPhotos(paginatedPhotos);
        keyMessage.textContent = '';
    } else {
        keyMessage.textContent = '密钥无效或已过期，请重试或联系管理员。';
    }
}