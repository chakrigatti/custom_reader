import { addRoute, navigate, startRouter } from "./router";
import { mountHeader } from "./components/header";
import { mountSidebar, refresh as refreshSidebar, setSelected } from "./components/sidebar";
import { mountArticleList, loadArticles, saveScroll } from "./components/article-list";
import { mountArticleDetail, showArticle } from "./components/article-detail";
import { mountAddFeedForm } from "./components/add-feed-form";

type View = "list" | "detail";
let currentView: View = "list";
let currentFeedId: number | null = null;

const headerEl = document.getElementById("header")!;
const sidebarEl = document.getElementById("sidebar")!;
const mainEl = document.getElementById("main")!;

// Mount components
mountHeader(headerEl, {
  onAddFeed: () => {
    mountAddFeedForm(document.getElementById("app")!, {
      onFeedAdded: () => {
        refreshSidebar();
        reloadCurrentList();
      },
      onCancel: () => {},
    });
  },
  onNavigateHome: () => navigate("/"),
  onSyncComplete: () => reloadCurrentList(),
});

mountSidebar(sidebarEl, {
  onSelectFeed: (feedId) => {
    if (feedId === null) {
      navigate("/");
    } else {
      navigate(`/feed/${feedId}`);
    }
  },
  onFeedDeleted: () => reloadCurrentList(),
});

mountArticleList(mainEl, {
  onSelectArticle: (id) => {
    saveScroll();
    navigate(`/article/${id}`);
  },
});

mountArticleDetail(mainEl, {
  onBack: () => {
    if (currentFeedId !== null) {
      navigate(`/feed/${currentFeedId}`);
    } else {
      navigate("/");
    }
  },
});

// Routes
addRoute("/", () => {
  currentView = "list";
  currentFeedId = null;
  setSelected(null);
  loadArticles();
});

addRoute("/feed/:id", (params) => {
  const feedId = Number(params.id);
  currentView = "list";
  currentFeedId = feedId;
  setSelected(feedId);
  loadArticles({ feed_id: feedId });
});

addRoute("/article/:id", (params) => {
  currentView = "detail";
  showArticle(Number(params.id));
});

function reloadCurrentList(): void {
  if (currentView === "list") {
    if (currentFeedId !== null) {
      loadArticles({ feed_id: currentFeedId });
    } else {
      loadArticles();
    }
  }
}

// When navigating back from detail to list, restore scroll
window.addEventListener("hashchange", () => {
  const hash = window.location.hash.slice(1) || "/";
  if (currentView === "detail" && !hash.startsWith("/article/")) {
    // Going back to list — will be handled by route, which calls loadArticles or restoreView
  }
});

startRouter();
