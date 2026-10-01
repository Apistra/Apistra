import { AdministrationApp } from "../../features/administration/public";

export default function BootstrapPage() {
  return <main className="installation-shell"><AdministrationApp initialView="bootstrap" /></main>;
}
