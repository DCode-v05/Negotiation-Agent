// NegotiBot AI Demo - JavaScript Implementation with Backend Integration

class NegotiBotDemo {
    constructor() {
        this.currentScreen = 'setup';
        this.selectedProduct = null;
        this.availableProducts = [];
        this.sessionId = null;
        this.websocket = null;
        this.negotiationData = {
            targetPrice: 7500,
            maxBudget: 9000,
            originalPrice: 10000,
            currentOffer: 10000,
            strategy: 'diplomatic',
            timeline: 'flexible',
            dealBreakers: '',
            productUrl: '',
            messagesExchanged: 0,
            startTime: null,
            endTime: null
        };
        
        // Backend API configuration
        this.apiBase = 'http://localhost:8000/api';
        this.wsBase = 'ws://localhost:8000/ws';
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        this.showScreen('setup');
        await this.loadProducts();
    }

    async loadProducts() {
        try {
            const response = await fetch(`${this.apiBase}/products`);
            if (!response.ok) {
                throw new Error('Failed to load products');
            }
            
            this.availableProducts = await response.json();
            this.renderProductSelection();
        } catch (error) {
            console.error('Error loading products:', error);
            this.showProductError('Failed to load products. Please check backend connection.');
        }
    }

    renderProductSelection() {
        const productSelection = document.getElementById('product-selection');
        
        if (this.availableProducts.length === 0) {
            productSelection.innerHTML = `
                <div class="loading-products">
                    <i class="fas fa-exclamation-triangle"></i> No products available
                </div>
            `;
            return;
        }

        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';
        
        this.availableProducts.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.dataset.productId = product.id;
            productCard.onclick = () => this.selectProduct(product);
            
            productCard.innerHTML = `
                <div class="product-card-header">
                    <h4 class="product-card-title">${product.title}</h4>
                    <span class="product-card-platform">${product.platform}</span>
                </div>
                <div class="product-card-price">₹${product.price.toLocaleString()}</div>
                <div class="product-card-details">
                    <strong>Seller:</strong> ${product.seller_name}<br>
                    <strong>Location:</strong> ${product.location}<br>
                    <strong>Category:</strong> ${product.category}
                </div>
                <span class="product-card-condition">${product.condition}</span>
            `;
            
            productsGrid.appendChild(productCard);
        });
        
        productSelection.innerHTML = '<h4 style="margin-bottom: 15px; color: #374151;">Choose a product to negotiate:</h4>';
        productSelection.appendChild(productsGrid);
    }

    selectProduct(product) {
        // Remove previous selection
        document.querySelectorAll('.product-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selection to clicked card
        document.querySelector(`[data-product-id="${product.id}"]`).classList.add('selected');
        
        // Store selected product
        this.selectedProduct = product;
        
        // Update form fields
        this.updateProductPreview(product);
        
        // Update negotiation data
        this.negotiationData.originalPrice = product.price;
        this.negotiationData.currentOffer = product.price;
        this.negotiationData.productUrl = product.url;
        
        // Update target price and max budget to reasonable defaults
        const targetPrice = Math.round(product.price * 0.75); // 25% discount target
        const maxBudget = Math.round(product.price * 0.9);   // 10% discount maximum
        
        document.getElementById('target-price').value = targetPrice;
        document.getElementById('max-budget').value = maxBudget;
        
        this.negotiationData.targetPrice = targetPrice;
        this.negotiationData.maxBudget = maxBudget;
    }

    updateProductPreview(product) {
        const productUrl = document.getElementById('product-url');
        const productPreview = document.getElementById('product-preview');
        
        // Update URL field
        productUrl.value = product.url;
        
        // Update preview
        document.getElementById('preview-title').textContent = product.title;
        document.getElementById('preview-price').textContent = `₹${product.price.toLocaleString()}`;
        document.getElementById('preview-seller').textContent = `Seller: ${product.seller_name}`;
        document.getElementById('preview-location').textContent = `Location: ${product.location}`;
        
        // Show preview
        productPreview.style.display = 'flex';
    }

    showProductError(message) {
        const productSelection = document.getElementById('product-selection');
        productSelection.innerHTML = `
            <div class="loading-products" style="color: #dc2626;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
    
    setupEventListeners() {
        // Strategy selection
        document.querySelectorAll('.strategy-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.strategy-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                this.negotiationData.strategy = option.dataset.strategy;
            });
        });
        
        // Form inputs
        document.getElementById('target-price').addEventListener('change', (e) => {
            this.negotiationData.targetPrice = parseInt(e.target.value) || 7500;
        });
        
        document.getElementById('max-budget').addEventListener('change', (e) => {
            this.negotiationData.maxBudget = parseInt(e.target.value) || 9000;
        });
        
        document.getElementById('timeline').addEventListener('change', (e) => {
            this.negotiationData.timeline = e.target.value;
        });
        
        document.getElementById('deal-breakers').addEventListener('change', (e) => {
            this.negotiationData.dealBreakers = e.target.value;
        });
    }
    
    showScreen(screenName) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(`${screenName}-screen`).classList.add('active');
        this.currentScreen = screenName;
    }
    
    async startNegotiation() {
        // Validate product selection
        if (!this.selectedProduct) {
            alert('Please select a product to negotiate for.');
            return;
        }

        try {
            this.negotiationData.startTime = new Date();
            this.showScreen('negotiation');
            this.updateProgress(0);
            this.updateCurrentOffer(this.negotiationData.originalPrice);
            this.updateAIStatus('Starting negotiation session...');

            // Start negotiation session with backend
            const response = await fetch(`${this.apiBase}/negotiations/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: this.selectedProduct.id,
                    target_price: this.negotiationData.targetPrice,
                    max_budget: this.negotiationData.maxBudget,
                    approach: this.negotiationData.strategy,
                    timeline: this.negotiationData.timeline,
                    special_requirements: this.negotiationData.dealBreakers
                })
            });

            if (!response.ok) {
                throw new Error('Failed to start negotiation session');
            }

            const sessionData = await response.json();
            this.sessionId = sessionData.session_id;

            this.updateAIStatus('Session created. Connecting to real-time chat...');

            // Connect to WebSocket for real-time communication
            await this.connectWebSocket();

            // Show session info and instructions
            this.showSessionInfo();

        } catch (error) {
            console.error('Error starting negotiation:', error);
            this.updateAIStatus('Failed to start session. Please try again.');
            alert('Failed to start negotiation. Please check your backend connection.');
        }
    }

    async connectWebSocket() {
        try {
            const wsUrl = `${this.wsBase}/user/${this.sessionId}`;
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('Connected to WebSocket');
                this.updateAIStatus('Connected! Waiting for seller to join...');
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket connection closed');
                this.updateAIStatus('Connection lost. Please refresh to reconnect.');
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateAIStatus('Connection error. Please try again.');
            };

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            throw error;
        }
    }

    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);

        switch (data.type) {
            case 'connected':
                this.updateAIStatus('Connected to session successfully!');
                break;

            case 'seller_online':
                this.updateAIStatus('Seller is online! AI negotiation will begin shortly...');
                break;

            case 'seller_offline':
                this.updateAIStatus('Seller went offline. Waiting for reconnection...');
                break;

            case 'message':
                if (data.sender === 'seller') {
                    this.addMessage(data.message.content, 'seller', true);
                }
                break;

            case 'ai_response':
                this.addMessage(data.message.content, 'ai', true);
                this.updateAIStatus('AI sent response. Waiting for seller...');
                break;

            case 'session_ended':
                this.handleSessionEnd(data.result);
                break;

            case 'error':
                this.updateAIStatus(`Error: ${data.message}`);
                break;
        }
    }

    showSessionInfo() {
        // Add session info to chat
        this.addMessage(
            `AI Agent initialized for ${this.selectedProduct.title}\n` +
            `Session ID: ${this.sessionId}\n` +
            `Target: ₹${this.negotiationData.targetPrice.toLocaleString()}\n` +
            `Max Budget: ₹${this.negotiationData.maxBudget.toLocaleString()}\n` +
            `Strategy: ${this.negotiationData.strategy}\n\n` +
            `Share this session ID with the seller to start negotiation.`,
            'system',
            false
        );
    }

    addMessage(content, sender, isRealTime = false) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
        
        let senderLabel = '';
        let messageClass = '';
        
        switch(sender) {
            case 'ai':
                senderLabel = 'AI Agent';
                messageClass = 'ai-message';
                break;
            case 'seller':
                senderLabel = 'Seller';
                messageClass = 'seller-message';
                break;
            case 'system':
                senderLabel = 'System';
                messageClass = 'system-message';
                break;
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender-name">${senderLabel}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-content ${messageClass}">${content}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        if (isRealTime) {
            this.negotiationData.messagesExchanged++;
            this.updateProgress(Math.min(this.negotiationData.messagesExchanged * 15, 90));
        }
    }

    handleSessionEnd(result) {
        this.updateAIStatus('Negotiation completed!');
        this.addMessage(
            `Session ended. Result: ${result.outcome}\n` +
            `Final outcome: ${result.outcome === 'success' ? 'Deal successful!' : 'No deal reached.'}`,
            'system',
            false
        );
        
        setTimeout(() => {
            if (result.outcome === 'success') {
                this.showSuccessResults(result);
            } else {
                this.showFailureResults(result);
            }
        }, 2000);
    }
    
    // Utility functions for progress tracking
    updateCurrentOffer(price) {
        document.getElementById('current-offer').textContent = `₹${price.toLocaleString()}`;
        const savings = this.negotiationData.originalPrice - price;
        document.getElementById('potential-savings').textContent = `₹${savings.toLocaleString()}`;
    }

    updateProgress(percentage) {
        document.getElementById('progress-fill').style.width = `${percentage}%`;
        document.getElementById('progress-text').textContent = `${Math.round(percentage)}% Complete`;
    }

    updateAIStatus(status) {
        document.getElementById('ai-status-text').textContent = status;
    }

    showSuccessResults(result) {
        this.negotiationData.endTime = new Date();
        this.showScreen('results');
        
        // Update results display
        document.querySelector('.results-summary h2').textContent = 'Negotiation Successful!';
        document.querySelector('.outcome-message').textContent = 'AI agent successfully secured a great deal for you!';
        document.querySelector('.original-price').textContent = `₹${this.negotiationData.originalPrice.toLocaleString()}`;
        document.querySelector('.final-price').textContent = `₹${result.final_price ? result.final_price.toLocaleString() : this.negotiationData.targetPrice.toLocaleString()}`;
        
        const savings = this.negotiationData.originalPrice - (result.final_price || this.negotiationData.targetPrice);
        const savingsPercent = Math.round((savings / this.negotiationData.originalPrice) * 100);
        
        document.querySelector('.savings-amount').textContent = `₹${savings.toLocaleString()}`;
        document.querySelector('.savings-percentage').textContent = `${savingsPercent}% saved`;
        
        const duration = Math.round((this.negotiationData.endTime - this.negotiationData.startTime) / 1000 / 60);
        document.querySelector('.negotiation-duration').textContent = `${duration} minutes`;
        document.querySelector('.messages-count').textContent = `${this.negotiationData.messagesExchanged} messages`;
    }

    showFailureResults(result) {
        this.negotiationData.endTime = new Date();
        this.showScreen('results');
        
        // Update results display for failure
        document.querySelector('.results-summary h2').textContent = 'Negotiation Incomplete';
        document.querySelector('.outcome-message').textContent = 'Unable to reach an agreement within your budget constraints.';
        document.querySelector('.original-price').textContent = `₹${this.negotiationData.originalPrice.toLocaleString()}`;
        document.querySelector('.final-price').textContent = 'No deal';
        document.querySelector('.savings-amount').textContent = '₹0';
        document.querySelector('.savings-percentage').textContent = '0% saved';
        
        const duration = Math.round((this.negotiationData.endTime - this.negotiationData.startTime) / 1000 / 60);
        document.querySelector('.negotiation-duration').textContent = `${duration} minutes`;
        document.querySelector('.messages-count').textContent = `${this.negotiationData.messagesExchanged} messages`;
    }

    // Control functions
    pauseNegotiation() {
        if (this.websocket) {
            this.updateAIStatus('Negotiation paused by user');
        }
    }

    takeOver() {
        this.updateAIStatus('User taking over negotiation');
        // Could implement manual message sending here
    }

    contactSeller() {
        if (this.selectedProduct) {
            const message = `Contact seller: ${this.selectedProduct.seller_contact}`;
            alert(message);
        }
    }

    newNegotiation() {
        // Reset everything and go back to setup
        this.selectedProduct = null;
        this.sessionId = null;
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.showScreen('setup');
        this.loadProducts(); // Reload products
    }
}

// Initialize the demo when page loads
let demo;
document.addEventListener('DOMContentLoaded', function() {
    demo = new NegotiBotDemo();
});

// Global functions for onclick handlers
function startNegotiation() {
    demo.startNegotiation();
}

function runScenario(scenarioType) {
    alert('Demo scenarios are disabled. Use real negotiation with seller interface.');
}

function pauseNegotiation() {
    demo.pauseNegotiation();
}

function takeOver() {
    demo.takeOver();
}

function contactSeller() {
    demo.contactSeller();
}

function newNegotiation() {
    demo.newNegotiation();
}