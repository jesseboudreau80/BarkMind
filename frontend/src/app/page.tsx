// Root / redirects to main layout home
import { redirect } from "next/navigation";

export default function Root() {
  redirect("/cases");
}
