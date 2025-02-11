export interface Configuration {
  id: number;
  user: string;
  name: string;
  private_key: string;
  public_key: string;
  preshared_key: string;
  ip: string;
}

export const fetchConfigurations = async () => {
  const res = await fetch("/api/wg/list");
  if (!res.ok) return null;

  const { data }: { data: Configuration[] } = await res.json();
  return data;
};

export const deleteConfiguration = async (id: number) => {
  const res = await fetch("/api/wg/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id })
  });
  return res.ok;
};

export const createConfiguration = async (name?: string) => {
  const res = await fetch("/api/wg/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  return res.ok;
};
