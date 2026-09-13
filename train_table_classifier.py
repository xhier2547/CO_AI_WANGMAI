from torchvision import datasets, transforms, models
from torch import nn, optim
import torch

# CONFIG
DATA_DIR = "dataset_tables"
MODEL_PATH = "table_classifier.pt"
EPOCHS = 10
BATCH_SIZE = 16
LR = 1e-4

# TRANSFORMS
transform = transforms.Compose([
    transforms.Resize((128,128)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3)
])

# LOAD DATA
dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
train_loader = torch.utils.data.DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# MODEL
device = "cuda" if torch.cuda.is_available() else "cpu"
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, 2)
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)

# TRAIN LOOP
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0
    for imgs, labels in train_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        out = model(imgs)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    print(f"Epoch [{epoch+1}/{EPOCHS}] Loss: {running_loss/len(train_loader):.4f}")

torch.save(model.state_dict(), MODEL_PATH)
print("✅ Model trained and saved as table_classifier.pt")
