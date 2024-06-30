import { useState } from "react";
import { Link } from "react-router-dom";
import { twMerge } from "tailwind-merge";

import GHButton from "./SideBar/GHButton";
import SideItem from "./SideBar/SideItem";
import useStudy from "../store/useStudy";
import { sidebarItemList } from "../routes/routes";

function RouteList() {
  const selectedStudy = useStudy((state) => state.studyName);

  return (
    <div className="flex flex-col gap-7">
      {sidebarItemList.map((item) => (
        <SideItem
          disabled={item.requiresStudy && !selectedStudy}
          key={item.label}
          to={item.path}
          icon={item.icon}
        >
          {item.label}
        </SideItem>
      ))}
    </div>
  );
}

function MobileNavBar() {
  const [open, setOpen] = useState<boolean>(false);

  const toggle = () => {
    setOpen(!open);
  };
  return (
    <nav className="bg-gradient-to-b z-20 items-center justify-between from-secondary-blue px-10 to-primary-blue w-full h-[80px] flex lg:hidden">
      <img className="w-40" src="/spt_logo.svg" alt="SPT logo" />
      <div
        className="w-12 cursor-pointer z-30 flex items-center justify-center h-12 rounded-full bg-white"
        onClick={toggle}
      >
        <div className={twMerge("menu", open && "menuOpen")}>
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
      <div
        className={twMerge(
          "absolute h-full w-[300px] p-5 pt-24 pr-0 bg-gradient-to-r from-secondary-blue lg:block to-primary-blue to-80% top-0 right-0 transition-transform duration-500",
          !open && "translate-x-[100%] hidden",
        )}
      >
        <RouteList />
      </div>
    </nav>
  );
}

function NavBar() {
  return (
    <nav className="bg-gradient-to-r from-secondary-blue hidden lg:block to-primary-blue to-80% [&>*]:ml-14 pt-14 border-r-[5px] border-secondary-yellow w-[330px] h-screen">
      <div>
        <Link to="/">
          <img className="mr-14" src="/spt_logo.svg" alt="SPT logo" />
        </Link>
      </div>
      <GHButton />
      <RouteList />
    </nav>
  );
}

export default function SideBar() {
  return (
    <>
      <MobileNavBar />
      <NavBar />
    </>
  );
}
