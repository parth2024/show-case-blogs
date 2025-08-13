window.EnhancedSmartImageQuill = {
    initialize: function(selector, options = {}) {
        try {
            const defaultOptions = {
                theme: 'snow',
                placeholder: options.placeholder || 'Write your content here...',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'color': ['#000000', '#6b7280', '#2563eb', '#059669', '#d97706', '#dc2626'] }],
                        [{ 'background': ['#fef3c7', '#dbeafe', '#d1fae5', '#fecaca', '#e5e7eb'] }],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'script': 'sub'}, { 'script': 'super' }],
                        [{ 'indent': '-1'}, { 'indent': '+1' }],
                        [{ 'align': [] }],
                        ['blockquote', 'code-block'],
                        ['link', 'image'],
                        ['clean']
                    ],
                    imageHandler: true
                }
            };

            const opts = Object.assign({}, defaultOptions, options);

            class ImageHandler {
                constructor(quill, options = {}) {
                    this.quill = quill;
                    this.options = options;

                    const toolbar = quill.getModule('toolbar');
                    if (toolbar) {
                        toolbar.addHandler('image', this.selectLocalImage.bind(this));
                    }

                    quill.root.addEventListener('paste', this.handlePaste.bind(this));
                    quill.root.addEventListener('drop', this.handleDrop.bind(this));
                }

                selectLocalImage() {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = 'image/*';
                    input.multiple = true;
                    input.click();

                    input.onchange = () => {
                        const files = Array.from(input.files || []);
                        if (files.length) this.uploadImages(files);
                    };
                }

                handlePaste(event) {
                    const clipboardData = event.clipboardData || window.clipboardData;
                    if (!clipboardData) return;
                    const items = clipboardData.items || [];
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].type && items[i].type.indexOf('image') !== -1) {
                            event.preventDefault();
                            const file = items[i].getAsFile();
                            if (file) this.uploadImages([file]);
                            break;
                        }
                    }
                }

                handleDrop(event) {
                    event.preventDefault();
                    const dt = event.dataTransfer;
                    if (!dt || !dt.files) return;
                    const files = Array.from(dt.files).filter(f => f.type && f.type.startsWith('image/'));
                    if (files.length) this.uploadImages(files);
                }

                uploadImages(files) {
                    if (!files || files.length === 0) return;
                    const formData = new FormData();
                    files.forEach((f) => formData.append('images', f));

                    const range = this.quill.getSelection(true) || { index: this.quill.getLength() };
                    const loadingText = 'Uploading images...';
                    this.quill.insertText(range.index, loadingText, { italic: true });

                    fetch('/upload-image/', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': window.EnhancedSmartImageQuill.getCsrfToken()
                        }
                    })
                        .then(resp => resp.json())
                        .then(data => {
                            try { this.quill.deleteText(range.index, loadingText.length); } catch (e) { console.warn(e); }

                            if (!data || !data.images || !Array.isArray(data.images) || data.images.length === 0) {
                                console.warn('No images returned from upload endpoint', data);
                                this.quill.insertText(range.index, 'Image upload failed or returned no images.', { color: '#dc2626' });
                                return;
                            }

                            data.images.forEach((imageData, idx) => {
                                const insertIndex = range.index + idx;
                                this.quill.insertEmbed(insertIndex, 'image', imageData.url);
                                this.quill.insertText(insertIndex + 1, '\n');
                                this.quill.setSelection(insertIndex + 2);
                                setTimeout(() => {
                                    try {
                                        const imgs = Array.from(this.quill.root.querySelectorAll('img')).reverse();
                                        const imgEl = imgs.find(im => im.src === imageData.url);
                                        if (imgEl && imageData.sizes) {
                                            imgEl.srcset = Object.entries(imageData.sizes).map(([size, url]) => `${url} ${size}w`).join(', ');
                                            imgEl.sizes = '(max-width: 768px) 100vw, 80vw';
                                        }
                                    } catch (ex) { console.warn('Failed to set srcset for uploaded image:', ex); }
                                }, 50);
                            });

                            setTimeout(() => {
                                try { window.EnhancedSmartImageQuill.classifyImages(this.quill.root); } catch (e) { console.warn(e); }
                            }, 120);
                        })
                        .catch(error => {
                            console.error('Upload failed:', error);
                            try { this.quill.deleteText(range.index, loadingText.length); } catch (e) {}
                            this.quill.insertText(range.index, 'Image upload failed. Please try again.', { color: '#dc2626' });
                        });
                }
            }

            Quill.register('modules/imageHandler', ImageHandler);

            const quill = new Quill(selector, opts);

            setTimeout(() => {
                try {
                    this.addTextColorTools(quill);
                    this.addHighlightTools(quill);
                } catch (ex) {
                    console.warn('Enhancement of toolbar pickers failed:', ex);
                }
            }, 50);

            return quill;
        } catch (err) {
            console.error('Quill initialization failed:', err);
            throw err;
        }
    },

    classifyImages: function(container) {
        const images = container.querySelectorAll('img:not(.classified)');
        images.forEach(img => {
            img.classList.add('classified', 'responsive-image');
            const figure = document.createElement('figure');
            figure.className = 'image-container';
            let figcaption = null;
            if (img.alt && img.alt.trim()) {
                figcaption = document.createElement('figcaption');
                figcaption.textContent = img.alt;
                figcaption.className = 'image-caption';
            }
            img.parentNode.insertBefore(figure, img);
            figure.appendChild(img);
            if (figcaption) figure.appendChild(figcaption);
        });
    },

    addLightboxToImage: function(img) {
        if (img.getAttribute('data-lightbox-added')) return;
        img.setAttribute('data-lightbox-added', 'true');
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', (e) => {
            e.preventDefault();
            const overlay = document.createElement('div');
            overlay.className = 'fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 cursor-pointer';
            const largeImg = document.createElement('img');
            largeImg.src = img.src;
            largeImg.alt = img.alt || '';
            largeImg.className = 'max-w-[90vw] max-h-[90vh] object-contain rounded-lg';
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '×';
            closeButton.className = 'absolute top-4 right-4 text-white text-4xl font-bold bg-black bg-opacity-50 rounded-full w-12 h-12 flex items-center justify-center';
            overlay.appendChild(largeImg);
            overlay.appendChild(closeButton);
            document.body.appendChild(overlay);
            const closeOverlay = () => {
                if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                document.removeEventListener('keydown', handleEscape);
            };
            const handleEscape = (ev) => { if (ev.key === 'Escape') closeOverlay(); };
            overlay.addEventListener('click', (ev) => { if (ev.target === overlay || ev.target === closeButton) closeOverlay(); });
            document.addEventListener('keydown', handleEscape);
        });
    },

    getCsrfToken: function() {
        const t = document.querySelector('[name=csrfmiddlewaretoken]');
        if (t && t.value) return t.value;
        const match = document.cookie.match(/(^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[2]) : '';
    },

    addTextColorTools: function(quill) {
        try {
            const container = quill.getModule('toolbar').container;
            const colorPicker = container.querySelector('.ql-color');
            if (!colorPicker) return;
            const colors = ['#111827','#6b7280','#2563eb','#059669','#d97706','#dc2626'];
            colorPicker.innerHTML = colors.map(color => `<span class="ql-picker-item" data-value="${color}" style="background-color: ${color};"></span>`).join('');
        } catch (e) { console.warn(e); }
    },

    addHighlightTools: function(quill) {
        try {
            const container = quill.getModule('toolbar').container;
            const backgroundPicker = container.querySelector('.ql-background');
            if (!backgroundPicker) return;
            const highlights = ['#fef3c7','#dbeafe','#d1fae5','#fecaca','#e5e7eb'];
            backgroundPicker.innerHTML = highlights.map(color => `<span class="ql-picker-item" data-value="${color}" style="background-color: ${color};"></span>`).join('');
        } catch (e) { console.warn(e); }
    },

    initLightbox: function() {
        document.querySelectorAll('.enhanced-article-content img').forEach(img => {
            img.addEventListener('click', () => {
                window.EnhancedSmartImageQuill.addLightboxToImage(img);
            });
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    try {
        document.querySelectorAll('.enhanced-article-content').forEach(container => {
            window.EnhancedSmartImageQuill.classifyImages(container);
            container.querySelectorAll('img').forEach(img => window.EnhancedSmartImageQuill.addLightboxToImage(img));
        });
    } catch (e) { console.warn(e); }
});