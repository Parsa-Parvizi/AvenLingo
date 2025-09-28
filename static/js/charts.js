/**
 * Simple Chart Library - جایگزین Chart.js
 * کتابخانه ساده برای ایجاد نمودارهای پایه
 */

class SimpleChart {
    constructor(canvas, config) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.config = config;
        this.data = config.data;
        this.options = config.options || {};
        
        // Set canvas size
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
        
        this.render();
    }
    
    render() {
        const type = this.config.type;
        
        switch (type) {
            case 'line':
                this.renderLineChart();
                break;
            case 'bar':
                this.renderBarChart();
                break;
            case 'doughnut':
            case 'pie':
                this.renderDoughnutChart();
                break;
            default:
                console.error('Chart type not supported:', type);
        }
    }
    
    renderLineChart() {
        const { labels, datasets } = this.data;
        const { width, height } = this.canvas;
        const padding = 40;
        const chartWidth = width - (padding * 2);
        const chartHeight = height - (padding * 2);
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Find min and max values
        let maxValue = 0;
        datasets.forEach(dataset => {
            const max = Math.max(...dataset.data);
            if (max > maxValue) maxValue = max;
        });
        
        // Draw grid lines
        this.ctx.strokeStyle = '#e9ecef';
        this.ctx.lineWidth = 1;
        
        // Vertical lines
        for (let i = 0; i <= labels.length - 1; i++) {
            const x = padding + (i * chartWidth / (labels.length - 1));
            this.ctx.beginPath();
            this.ctx.moveTo(x, padding);
            this.ctx.lineTo(x, height - padding);
            this.ctx.stroke();
        }
        
        // Horizontal lines
        for (let i = 0; i <= 5; i++) {
            const y = padding + (i * chartHeight / 5);
            this.ctx.beginPath();
            this.ctx.moveTo(padding, y);
            this.ctx.lineTo(width - padding, y);
            this.ctx.stroke();
        }
        
        // Draw datasets
        datasets.forEach((dataset, datasetIndex) => {
            this.ctx.strokeStyle = dataset.borderColor || '#1f3a93';
            this.ctx.fillStyle = dataset.backgroundColor || 'rgba(31, 58, 147, 0.1)';
            this.ctx.lineWidth = dataset.borderWidth || 2;
            
            // Draw line
            this.ctx.beginPath();
            dataset.data.forEach((value, index) => {
                const x = padding + (index * chartWidth / (labels.length - 1));
                const y = height - padding - (value / maxValue * chartHeight);
                
                if (index === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            });
            this.ctx.stroke();
            
            // Fill area under line
            if (dataset.fill) {
                this.ctx.lineTo(width - padding, height - padding);
                this.ctx.lineTo(padding, height - padding);
                this.ctx.closePath();
                this.ctx.fill();
            }
            
            // Draw points
            dataset.data.forEach((value, index) => {
                const x = padding + (index * chartWidth / (labels.length - 1));
                const y = height - padding - (value / maxValue * chartHeight);
                
                this.ctx.beginPath();
                this.ctx.arc(x, y, 4, 0, 2 * Math.PI);
                this.ctx.fillStyle = dataset.borderColor || '#1f3a93';
                this.ctx.fill();
            });
        });
        
        // Draw labels
        this.ctx.fillStyle = '#495057';
        this.ctx.font = '12px Vazir';
        this.ctx.textAlign = 'center';
        
        labels.forEach((label, index) => {
            const x = padding + (index * chartWidth / (labels.length - 1));
            this.ctx.fillText(label, x, height - 10);
        });
        
        // Draw y-axis labels
        this.ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const value = Math.round((maxValue / 5) * (5 - i));
            const y = padding + (i * chartHeight / 5) + 4;
            this.ctx.fillText(value.toString(), padding - 10, y);
        }
    }
    
    renderBarChart() {
        const { labels, datasets } = this.data;
        const { width, height } = this.canvas;
        const padding = 40;
        const chartWidth = width - (padding * 2);
        const chartHeight = height - (padding * 2);
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Find max value
        let maxValue = 0;
        datasets.forEach(dataset => {
            const max = Math.max(...dataset.data);
            if (max > maxValue) maxValue = max;
        });
        
        const barWidth = chartWidth / labels.length * 0.8;
        const barSpacing = chartWidth / labels.length * 0.2;
        
        // Draw bars
        datasets.forEach((dataset, datasetIndex) => {
            this.ctx.fillStyle = dataset.backgroundColor || '#1f3a93';
            
            dataset.data.forEach((value, index) => {
                const barHeight = (value / maxValue) * chartHeight;
                const x = padding + (index * (barWidth + barSpacing)) + (barSpacing / 2);
                const y = height - padding - barHeight;
                
                this.ctx.fillRect(x, y, barWidth, barHeight);
            });
        });
        
        // Draw labels
        this.ctx.fillStyle = '#495057';
        this.ctx.font = '12px Vazir';
        this.ctx.textAlign = 'center';
        
        labels.forEach((label, index) => {
            const x = padding + (index * (barWidth + barSpacing)) + (barSpacing / 2) + (barWidth / 2);
            this.ctx.fillText(label, x, height - 10);
        });
        
        // Draw y-axis labels
        this.ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const value = Math.round((maxValue / 5) * (5 - i));
            const y = padding + (i * chartHeight / 5) + 4;
            this.ctx.fillText(value.toString(), padding - 10, y);
        }
    }
    
    renderDoughnutChart() {
        const { labels, datasets } = this.data;
        const { width, height } = this.canvas;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 20;
        const innerRadius = this.config.type === 'doughnut' ? radius * 0.6 : 0;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        const dataset = datasets[0];
        const total = dataset.data.reduce((sum, value) => sum + value, 0);
        
        let currentAngle = -Math.PI / 2; // Start from top
        
        dataset.data.forEach((value, index) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            const color = dataset.backgroundColor[index] || this.getDefaultColor(index);
            
            // Draw slice
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            if (innerRadius > 0) {
                this.ctx.arc(centerX, centerY, innerRadius, currentAngle + sliceAngle, currentAngle, true);
            } else {
                this.ctx.lineTo(centerX, centerY);
            }
            this.ctx.closePath();
            this.ctx.fillStyle = color;
            this.ctx.fill();
            
            currentAngle += sliceAngle;
        });
        
        // Draw legend
        this.drawLegend(labels, dataset.backgroundColor);
    }
    
    drawLegend(labels, colors) {
        const { width, height } = this.canvas;
        const legendX = width - 120;
        const legendY = 20;
        
        this.ctx.font = '12px Vazir';
        this.ctx.textAlign = 'right';
        
        labels.forEach((label, index) => {
            const y = legendY + (index * 20);
            const color = colors[index] || this.getDefaultColor(index);
            
            // Draw color box
            this.ctx.fillStyle = color;
            this.ctx.fillRect(legendX, y, 12, 12);
            
            // Draw label
            this.ctx.fillStyle = '#495057';
            this.ctx.fillText(label, legendX - 5, y + 9);
        });
    }
    
    getDefaultColor(index) {
        const colors = [
            '#1f3a93',
            '#48c9b0',
            '#f39c12',
            '#e74c3c',
            '#9b59b6',
            '#34495e',
            '#16a085',
            '#f1c40f'
        ];
        return colors[index % colors.length];
    }
    
    // Method to update chart data
    update(newData) {
        this.data = newData;
        this.render();
    }
    
    // Method to destroy chart
    destroy() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

// Helper function to create charts (similar to Chart.js API)
function createChart(canvas, config) {
    if (typeof canvas === 'string') {
        canvas = document.getElementById(canvas);
    }
    
    return new SimpleChart(canvas, config);
}

// Export for use
window.SimpleChart = SimpleChart;
window.createChart = createChart;

// Animation utilities
class ChartAnimations {
    static fadeIn(element, duration = 500) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    static slideUp(element, duration = 300) {
        const height = element.offsetHeight;
        element.style.height = '0px';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        let start = null;
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const currentHeight = Math.min((progress / duration) * height, height);
            
            element.style.height = currentHeight + 'px';
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.height = '';
                element.style.overflow = '';
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    static countUp(element, endValue, duration = 1000) {
        const startValue = 0;
        let start = null;
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const currentValue = Math.min((progress / duration) * endValue, endValue);
            
            element.textContent = Math.floor(currentValue).toLocaleString('fa-IR');
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
}

window.ChartAnimations = ChartAnimations; 