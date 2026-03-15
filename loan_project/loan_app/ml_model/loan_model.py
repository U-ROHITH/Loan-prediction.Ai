import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import plot_model
import matplotlib.pyplot as plt
import joblib
import os

# Load dataset
df = pd.read_csv('loan_app/ml_model/personal_loan_dataset_updated.csv')

# Smart feature: ApprovalBoost (just as feature, not label editor)
def apply_custom_weights(row):
    score = 0
    if 25 <= row['Age'] <= 60:
        score += 1
    if row['Credit Score'] > 700:
        score += 1
    if row['Employment_employed'] == 1:
        score += 1
    if row['Residence_owned'] == 1:
        score += 1
    if row['Existing Loans'] <= row['Annual Income'] * 0.4:
        score += 1
    if row['Existing Loans'] <= row['Monthly Expenses'] * 12:
        score += 1
    return score

df['ApprovalBoost'] = df.apply(apply_custom_weights, axis=1)

# Separate features and target
X = df.drop('Loan Approved', axis=1)
y = df['Loan Approved']

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Calculate class weights to handle imbalance
class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y), y=y)
class_weights = dict(enumerate(class_weights))

# Build ANN model
model = Sequential([
    Dense(128, activation='relu', input_shape=(X.shape[1],)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Early stopping
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train model
history = model.fit(X_train, y_train, epochs=100, batch_size=32,
                    validation_data=(X_test, y_test),
                    callbacks=[early_stop],
                    class_weight=class_weights)

# Save model and scaler
model.save('loan_app/ml_model/loan_ann_model.h5')
joblib.dump(scaler, 'loan_app/ml_model/scaler.pkl')

# Create plot dir
plot_dir = 'loan_app/static/loan_app/plots'
os.makedirs(plot_dir, exist_ok=True)

# Accuracy and Loss Plot
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train')
plt.plot(history.history['val_accuracy'], label='Val')
plt.title("Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train')
plt.plot(history.history['val_loss'], label='Val')
plt.title("Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.tight_layout()
plt.savefig(f'{plot_dir}/ann_loss_accuracy.png')
plt.close()

# Confusion Matrix
y_pred = (model.predict(X_test) > 0.5).astype("int32")
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot()
plt.title("Confusion Matrix")
plt.savefig(f'{plot_dir}/confusion_matrix.png')
plt.close()

# ANN Architecture
plot_model(model, to_file=f'{plot_dir}/ann_architecture.png', show_shapes=True)
