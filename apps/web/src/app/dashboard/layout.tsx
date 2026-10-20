import React from "react";
import { AppProviders } from "../../components/AppProviders";
import { Footer } from "../../components/Footer";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <AppProviders>{children}</AppProviders>
      <Footer />
    </>
  );
}
