import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://whats-screening-to.ca",
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1,
    },
  ];
}
