import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load the real dataset
df = pd.read_csv("C:\\Users\\ROHIT\\OneDrive\\Desktop\\RealEstate\\data.csv")

# 2. Look at the column names to see what we have
print(df.columns)

# 3. Quick check: What are the average rents in different cities?
city_rent = df.groupby('city')['rent'].mean().sort_values(ascending=False)
print("\nAverage Rent by City:")
print(city_rent)

# Create a visual chart
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x='city', y='rent', hue='furnishing')
plt.title('How Rent Varies by City and Furnishing Status')
plt.ylabel('Rent (in Currency)')
plt.xticks(rotation=45) # Tilts city names so they don't overlap
plt.show()