/**
 * 前端性能监控和内存优化工具
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = {
      memory: {
        used: 0,
        total: 0,
        peak: 0
      },
      timing: {
        pageLoad: 0,
        domReady: 0,
        resources: 0
      },
      components: new Map()
    }
    
    this.observers = []
    this.init()
  }

  init() {
    // 页面加载完成后启动监控
    if (document.readyState === 'complete') {
      this.startMonitoring()
    } else {
      window.addEventListener('load', () => this.startMonitoring())
    }
  }

  startMonitoring() {
    // 监控内存使用
    this.monitorMemory()
    
    // 监控页面性能
    this.monitorPagePerformance()
    
    // 监控大型组件
    this.monitorComponentPerformance()
    
    // 定期清理
    this.startCleanupTimer()
  }

  monitorMemory() {
    if (performance.memory) {
      const updateMemory = () => {
        const memory = performance.memory
        this.metrics.memory = {
          used: Math.round(memory.usedJSHeapSize / 1024 / 1024), // MB
          total: Math.round(memory.totalJSHeapSize / 1024 / 1024), // MB
          peak: Math.max(this.metrics.memory.peak, Math.round(memory.usedJSHeapSize / 1024 / 1024))
        }
        
        // 内存使用超过阈值时发出警告
        if (this.metrics.memory.used > 200) {
          console.warn(`⚠️ 内存使用过高: ${this.metrics.memory.used}MB`)
          this.triggerGarbageCollection()
        }
      }
      
      // 每30秒检查一次内存使用
      setInterval(updateMemory, 30000)
      updateMemory()
    }
  }

  monitorPagePerformance() {
    if (performance.timing) {
      const timing = performance.timing
      this.metrics.timing = {
        pageLoad: timing.loadEventEnd - timing.navigationStart,
        domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
        resources: timing.loadEventEnd - timing.domContentLoadedEventEnd
      }
    }
  }

  monitorComponentPerformance() {
    // 监控组件渲染性能
    if (window.performance && window.performance.observer) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'measure' && entry.name.includes('Vue')) {
            this.metrics.components.set(entry.name, {
              duration: entry.duration,
              startTime: entry.startTime
            })
          }
        }
      })
      
      try {
        observer.observe({ entryTypes: ['measure'] })
        this.observers.push(observer)
      } catch (e) {
        // 浏览器不支持时忽略
      }
    }
  }

  triggerGarbageCollection() {
    // 手动触发垃圾回收（如果支持）
    if (window.gc && typeof window.gc === 'function') {
      window.gc()
    }
    
    // 清理可能的内存泄漏
    this.cleanupEventListeners()
    this.cleanupTimers()
  }

  cleanupEventListeners() {
    // 清理未移除的事件监听器（这里是示例，实际需要组件配合）
    const elements = document.querySelectorAll('[data-cleanup-listeners]')
    elements.forEach(el => {
      const events = el.dataset.cleanupListeners?.split(',') || []
      events.forEach(event => {
        el.removeEventListener(event, () => {}, true)
      })
    })
  }

  cleanupTimers() {
    // 清理可能遗留的定时器（需要组件配合注册）
    if (window.activeTimers) {
      window.activeTimers.forEach(timerId => {
        clearTimeout(timerId)
        clearInterval(timerId)
      })
      window.activeTimers.clear()
    }
  }

  startCleanupTimer() {
    // 每5分钟进行一次内存清理
    setInterval(() => {
      if (this.metrics.memory.used > 150) {
        this.triggerGarbageCollection()
      }
    }, 300000) // 5分钟
  }

  getMetrics() {
    return {
      ...this.metrics,
      timestamp: Date.now()
    }
  }

  destroy() {
    // 清理监控器
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
  }
}

// 内存优化工具
export class MemoryOptimizer {
  static optimizeImages() {
    // 优化图片加载
    const images = document.querySelectorAll('img[data-src]')
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target
          img.src = img.dataset.src
          img.removeAttribute('data-src')
          imageObserver.unobserve(img)
        }
      })
    })
    
    images.forEach(img => imageObserver.observe(img))
    return imageObserver
  }

  static limitArraySize(array, maxSize = 1000) {
    // 限制数组大小，防止内存过载
    if (array.length > maxSize) {
      return array.slice(-maxSize)
    }
    return array
  }

  static debounce(func, wait) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }

  static throttle(func, limit) {
    let inThrottle
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => inThrottle = false, limit)
      }
    }
  }
}

// 创建全局性能监控实例
export const performanceMonitor = new PerformanceMonitor()

// 开发模式下在控制台显示性能信息
if (import.meta.env.DEV) {
  window.performanceMonitor = performanceMonitor
  
  // 每分钟在控制台输出性能指标
  setInterval(() => {
    const metrics = performanceMonitor.getMetrics()
    console.group('📊 性能指标')
    console.log(`内存使用: ${metrics.memory.used}MB / ${metrics.memory.total}MB`)
    console.log(`峰值内存: ${metrics.memory.peak}MB`)
    console.log(`页面加载: ${metrics.timing.pageLoad}ms`)
    console.log(`DOM就绪: ${metrics.timing.domReady}ms`)
    console.groupEnd()
  }, 60000)
}

export default PerformanceMonitor 