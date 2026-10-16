import "./globals.css";
import type { ReactNode } from "react";
export const metadata = {title: "VietDub AI · 制作工作台", description: "授权短剧中越配音制作"};
export default function Layout({children}: {children: ReactNode}) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
