import { QueryClient, QueryClientProvider } from "react-query";
import SideBar from "./components/SideBar";
import Router from "./Router";

const queryClient = new QueryClient();

function App() {
  return (
    <>
      <QueryClientProvider client={queryClient}>
        <main className="flex flex-col lg:flex-row">
          <SideBar />
          <Router />
        </main>
      </QueryClientProvider>
    </>
  );
}

export default App;
