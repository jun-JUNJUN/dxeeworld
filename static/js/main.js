// Startup Platform:Dxee - Main JavaScript

document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle functionality
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebar-toggle");

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("collapsed");

      // Store sidebar state in localStorage
      const isCollapsed = sidebar.classList.contains("collapsed");
      localStorage.setItem("sidebarCollapsed", isCollapsed);
    });
  }

  // Restore sidebar state from localStorage
  const savedSidebarState = localStorage.getItem("sidebarCollapsed");
  if (savedSidebarState === "true") {
    sidebar.classList.add("collapsed");
  }

  // Add smooth scrolling for internal links
  const internalLinks = document.querySelectorAll('a[href^="#"]');
  internalLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const targetId = this.getAttribute("href");
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    });
  });

  // Active navigation item highlighting
  const navLinks = document.querySelectorAll(".nav-link");
  const currentPath = window.location.pathname;

  navLinks.forEach((link) => {
    // Skip links without href attribute (e.g., buttons with onclick)
    if (!link.href) {
      return;
    }

    try {
      const linkPath = new URL(link.href).pathname;
      if (linkPath === currentPath) {
        link.classList.add("active");
      }
    } catch (error) {
      // Ignore invalid URLs
      console.debug("Skipping invalid link:", link);
    }
  });

  // Form validation helpers
  function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  function showMessage(message, type = "info") {
    // Create message element
    const messageEl = document.createElement("div");
    messageEl.className = `message message-${type}`;
    messageEl.textContent = message;

    // Style the message
    messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 9999;
            transition: opacity 0.3s ease;
        `;

    // Set background color based on type
    switch (type) {
      case "success":
        messageEl.style.backgroundColor = "#22c55e";
        break;
      case "error":
        messageEl.style.backgroundColor = "#ef4444";
        break;
      case "warning":
        messageEl.style.backgroundColor = "#f59e0b";
        break;
      default:
        messageEl.style.backgroundColor = "#3b82f6";
    }

    // Add to page
    document.body.appendChild(messageEl);

    // Remove after 3 seconds
    setTimeout(() => {
      messageEl.style.opacity = "0";
      setTimeout(() => {
        document.body.removeChild(messageEl);
      }, 300);
    }, 3000);
  }

  // ===== LOGIN STATE MANAGEMENT =====

  // ログイン状態管理
  function getCurrentUser() {
    // localStorage or sessionStorage からユーザー情報を取得
    const userStr =
      localStorage.getItem("user") || sessionStorage.getItem("user");
    return userStr ? JSON.parse(userStr) : null;
  }

  async function updateLoginUI() {
    const loginPrompt = document.getElementById("login-prompt");
    const userInfo = document.getElementById("user-info");
    let user = getCurrentUser();

    // Debug logging
    console.log("updateLoginUI called");
    console.log("User data from localStorage:", user);

    // If no user in localStorage, try to fetch from server
    if (!user) {
      console.log("No user in localStorage, fetching from server...");
      try {
        const response = await fetch("/api/user/info");
        const data = await response.json();

        if (response.ok && data.authenticated) {
          user = data.user;
          // Save to localStorage for future use
          localStorage.setItem("user", JSON.stringify(user));
          console.log("User data fetched from server and saved:", user);
        } else {
          console.log("Not authenticated on server");
        }
      } catch (error) {
        console.error("Failed to fetch user info:", error);
      }
    }

    if (loginPrompt && userInfo) {
      if (user) {
        // ログイン済みの場合
        console.log("User is logged in, showing user info");
        loginPrompt.style.display = "none";
        userInfo.style.display = "block";

        // ユーザー情報を更新
        const userNameEl = document.getElementById("user-name");
        const userEmailEl = document.getElementById("user-email");
        const userAvatarEl = document.getElementById("user-avatar");

        if (userNameEl) userNameEl.textContent = user.name || "Unknown User";
        if (userEmailEl) {
          // Use email_masked from server (already masked in MongoDB)
          const displayEmail = user.email_masked || user.email || "";
          console.log("Setting email display to:", displayEmail);
          userEmailEl.textContent = displayEmail;

          // Set full email as title for hover (if available and different)
          if (user.email && user.email !== displayEmail) {
            userEmailEl.title = user.email;
          }
        }
        if (userAvatarEl) {
          userAvatarEl.src = user.avatar || "/static/images/default-avatar.svg";
          userAvatarEl.alt = `${user.name || "User"}のアバター`;
        }
      } else {
        // 未ログインの場合
        console.log("No user data, showing login prompt");
        loginPrompt.style.display = "block";
        userInfo.style.display = "none";
      }
    } else {
      console.error(
        "Required elements not found - loginPrompt:",
        loginPrompt,
        "userInfo:",
        userInfo,
      );
    }
  }

  function openLoginPanel() {
    const loginPanel = document.getElementById("login-mini-panel");
    if (loginPanel) {
      loginPanel.style.display = "block";
      loginPanel.setAttribute("aria-hidden", "false");

      // フォーカスをパネル内の最初の要素に移動
      const firstInput = loginPanel.querySelector("input, button");
      if (firstInput) {
        firstInput.focus();
      }

      // パネル外クリックで閉じる
      setTimeout(() => {
        document.addEventListener("click", function closePanel(event) {
          if (
            !loginPanel.contains(event.target) &&
            !event.target.closest(".login-btn")
          ) {
            loginPanel.style.display = "none";
            loginPanel.setAttribute("aria-hidden", "true");
            document.removeEventListener("click", closePanel);
          }
        });
      }, 100);
    }
  }

  async function logout() {
    // ログアウト処理
    try {
      // First, call server to invalidate session
      const response = await fetch("/logout", {
        method: "GET",
        credentials: "include",
      });

      // Clear local storage
      localStorage.removeItem("user");
      sessionStorage.removeItem("user");

      // Update UI to show login button
      await updateLoginUI();

      showMessage("ログアウトしました", "success");

      // Redirect to home page after a short delay
      setTimeout(() => {
        window.location.href = "/";
      }, 1000);
    } catch (error) {
      console.error("Logout error:", error);
      // Even if server logout fails, clear local data
      localStorage.removeItem("user");
      sessionStorage.removeItem("user");
      await updateLoginUI();
      showMessage("ログアウトしました", "success");
    }
  }

  function setUser(userData) {
    // ユーザー情報をローカルストレージに保存
    localStorage.setItem("user", JSON.stringify(userData));
    updateLoginUI();
    showMessage(`${userData.name}さん、ログインしました`, "success");
  }

  // Floating cards animation (if hero section exists)
  const floatingCards = document.querySelectorAll(".floating-cards .card");
  if (floatingCards.length > 0) {
    // Add subtle floating animation
    floatingCards.forEach((card, index) => {
      const animationDelay = index * 0.5;
      card.style.animation = `float 3s ease-in-out ${animationDelay}s infinite`;
    });

    // Add CSS animation keyframes
    const style = document.createElement("style");
    style.textContent = `
            @keyframes float {
                0%, 100% {
                    transform: translateY(0px);
                }
                50% {
                    transform: translateY(-10px);
                }
            }
        `;
    document.head.appendChild(style);
  }

  // Intersection Observer for scroll animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("fade-in");
      }
    });
  }, observerOptions);

  // Observe elements for animations
  const animatedElements = document.querySelectorAll(
    ".feature-card, .stat-item",
  );
  animatedElements.forEach((el) => {
    observer.observe(el);
  });

  // Add fade-in animation CSS
  const fadeStyle = document.createElement("style");
  fadeStyle.textContent = `
        .feature-card, .stat-item {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }

        .feature-card.fade-in, .stat-item.fade-in {
            opacity: 1;
            transform: translateY(0);
        }
    `;
  document.head.appendChild(fadeStyle);

  // Initialize login UI on page load
  updateLoginUI();

  // Expose utilities globally
  window.StartupPlatform = {
    validateEmail,
    showMessage,
    getCurrentUser,
    updateLoginUI,
    openLoginPanel,
    logout,
    setUser,
  };

  // Expose functions globally for inline onclick handlers in HTML
  window.openLoginPanel = openLoginPanel;
  window.logout = logout;
});
