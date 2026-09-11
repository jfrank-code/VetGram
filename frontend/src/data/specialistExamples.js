// Sample photos for the "Try a sample photo" quick action in Breed ID and
// Skin Screening (Wikimedia Commons, freely licensed). Both the specialist
// model and GPT-4o-mini now run for real against whatever image is sent —
// this file no longer holds any mocked result data, only the photos.

const BREED_SAMPLE_IMAGES = [
  'https://commons.wikimedia.org/wiki/Special:FilePath/YellowLabradorLooking_new.jpg',
  'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Border_Collie_600.jpg/500px-Border_Collie_600.jpg',
  'https://commons.wikimedia.org/wiki/Special:FilePath/Domestic_Cat_Face_Shot.jpg',
]

// Ordinary, non-graphic pet close-ups (not actual lesion photos) — sourcing
// real dermatology images raises its own licensing/appropriateness
// questions, so these are just for demoing the flow, not for evaluating
// the trained model's real accuracy.
const SKIN_SAMPLE_IMAGES = [
  'https://commons.wikimedia.org/wiki/Special:FilePath/YellowLabradorLooking_new.jpg',
  'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Border_Collie_600.jpg/500px-Border_Collie_600.jpg',
  'https://commons.wikimedia.org/wiki/Special:FilePath/Domestic_Cat_Face_Shot.jpg',
]

export function getBreedSampleImage(index) {
  return BREED_SAMPLE_IMAGES[index % BREED_SAMPLE_IMAGES.length]
}

export function getSkinSampleImage(index) {
  return SKIN_SAMPLE_IMAGES[index % SKIN_SAMPLE_IMAGES.length]
}
