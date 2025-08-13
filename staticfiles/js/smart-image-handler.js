/* 
   FILE 1: blog/static/blog/js/smart-image-handler.js
   
   This JavaScript file should be created in your blog/static/blog/js/ directory
*/

// Custom Image Blot for Smart Container Handling
const BlockEmbed = Quill.import('blots/block/embed');

class SmartImageBlot extends BlockEmbed {
    static blotName = 'smartImage';
    static tagName = 'div';
    static className = 'image-container';
    
    static create(value) {
        const node = super.create();
        node.setAttribute('class', `image-container-${value.layout || 'single'}`);
        
        if (Array.isArray(value.src)) {
            // Multiple images - create gallery
            value.src.forEach(src => {
                const img = document.createElement('img');
                img.setAttribute('src', src);
                img.setAttribute('alt', value.alt || '');
                img.setAttribute('loading', 'lazy'); // Performance optimization
                node.appendChild(img);
            });
        } else {
            // Single image
            const img = document.createElement('img');
            img.setAttribute('src', value.src);
            img.setAttribute('alt', value.alt || '');
            img.setAttribute('loading', 'lazy');
            node.appendChild(img);
        }
        
        return node;
    }
    
    static value(node) {
        const images = node.querySelectorAll('img');
        const layout = node.className.replace('image-container-', '');
        
        if (images.length === 1) {
            return {
                src: images[0].getAttribute('src'),
                alt: images[0].getAttribute('alt') || '',
                layout: layout
            };
        } else {
            return {
                src: Array.from(images).map(img => img.getAttribute('src')),
                alt: images[0]?.getAttribute('alt') || '',
                layout: layout
            };
        }
    }
}

// Register the custom blot
Quill.register(SmartImageBlot);

// Smart Image Handler Function
function createSmartImageHandler() {
    return function imageHandler() {
        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        input.setAttribute('accept', 'image/*');
        input.setAttribute('multiple', true);
        input.click();
        
        input.onchange = () => {
            const files = Array.from(input.files);
            if (files.length === 0) return;
            
            // Show loading indicator
            const range = this.quill.getSelection();
            if (!range) return;
            
            this.quill.insertText(range.index, 'Uploading images...', 'italic');
            
            // Process each file
            const imagePromises = files.map(file => {
                return new Promise((resolve) => {
                    // Here you would typically upload to your server
                    // For now, we'll use FileReader for demo
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.readAsDataURL(file);
                });
            });
            
            Promise.all(imagePromises).then(imageSrcs => {
                // Remove loading text
                this.quill.deleteText(range.index, 'Uploading images...'.length);
                
                // Insert smart image container
                const layout = determineLayout(imageSrcs.length);
                
                if (imageSrcs.length === 1) {
                    this.quill.insertEmbed(range.index, 'smartImage', {
                        src: imageSrcs[0],
                        layout: layout,
                        alt: 'Uploaded image'
                    });
                } else {
                    this.quill.insertEmbed(range.index, 'smartImage', {
                        src: imageSrcs,
                        layout: layout,
                        alt: 'Gallery images'
                    });
                }
                
                // Move cursor after the image
                this.quill.setSelection(range.index + 1);
            });
        };
    };
}

// Layout Determination Logic
function determineLayout(imageCount) {
    if (imageCount === 1) {
        return 'single';
    } else if (imageCount <= 3) {
        return 'gallery';
    } else {
        return 'grid';
    }
}

// Initialize Quill with Smart Image Handler
function initializeSmartQuill(selector, options = {}) {
    const defaultOptions = {
        theme: 'snow',
        placeholder: 'Write your masterpiece here...',
        modules: {
            toolbar: {
                container: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    ['blockquote', 'code-block'],
                    [{'list': 'ordered'}, {'list': 'bullet'}],
                    [{ 'script': 'sub'}, { 'script': 'super' }],
                    [{ 'indent': '-1'}, { 'indent': '+1' }],
                    ['link', 'image'],
                    ['clean']
                ],
                handlers: {
                    image: createSmartImageHandler()
                }
            }
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    return new Quill(selector, finalOptions);
}

// Export for global use
window.SmartImageQuill = {
    initialize: initializeSmartQuill,
    SmartImageBlot: SmartImageBlot
};
