export interface DetectedFoodItem {
  name: string;
  confidence: number;
  bounding_box?: { x: number; y: number; width: number; height: number };
  estimated_portion_grams?: number;
}

export interface MacronutrientEstimate {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface FoodItemNutrition {
  food_item: DetectedFoodItem;
  nutrition: MacronutrientEstimate;
}

export interface NutritionResult {
  report_id?: number;
  photo_url?: string;
  detected_items: FoodItemNutrition[];
  total_nutrition: MacronutrientEstimate;
  menu_composition?: Record<string, number>;
  meets_standard?: boolean;
  analysis_notes?: string;
}
